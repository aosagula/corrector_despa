import ollama
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..core.config import settings
from .prompt_service import PromptService
import json
import logging
import re

logger = logging.getLogger(__name__)


class LlamaService:
    """Servicio para interactuar con el modelo Phi-4 a través de Ollama"""

    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL

    @staticmethod
    def clean_json_response(text: str) -> str:
        """
        Limpia y corrige problemas comunes en JSON generado por LLM

        Args:
            text: Texto JSON potencialmente malformado

        Returns:
            Texto JSON corregido
        """
        # Remover texto antes/después del JSON
        text = text.strip()

        # Reemplazar comillas tipográficas por comillas normales
        # " " → " (U+201C, U+201D → U+0022)
        # ' ' → ' (U+2018, U+2019 → U+0027)
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        # Remover caracteres de control invisibles (excepto \n, \r, \t)
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

        # Normalizar espacios en blanco
        text = re.sub(r'[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]', ' ', text)

        # Remover comentarios de JavaScript/C++ (// comentario)
        # Solo remover si está fuera de strings
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Buscar // que no esté dentro de un string
            in_string = False
            escape_next = False
            comment_start = -1

            for i, char in enumerate(line):
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not in_string:
                    in_string = True
                elif char == '"' and in_string:
                    in_string = False
                elif char == '/' and i + 1 < len(line) and line[i + 1] == '/' and not in_string:
                    comment_start = i
                    break

            if comment_start >= 0:
                cleaned_lines.append(line[:comment_start].rstrip())
            else:
                cleaned_lines.append(line)

        text = '\n'.join(cleaned_lines)

        # Remover expresiones JavaScript (ej: 2000 + (2 * 42) + 1)
        # Reemplazar por null si está en contexto de valor
        text = re.sub(r':\s*([0-9]+\s*[\+\-\*\/]\s*[0-9()\s\+\-\*\/]+)', ': null', text)

        # Convertir números mal formateados a strings
        # Solo números con comas DENTRO del número (ej: 1.234,56 o 30,40)
        # NO convertir números válidos como 0.95
        def quote_malformed_number(match):
            value = match.group(1)
            # Si tiene coma DENTRO (no al final) o más de un punto → es mal formado
            if (',' in value and not value.endswith(',')) or value.count('.') > 1:
                # Remover coma del final si existe
                clean_value = value.rstrip(',')
                return f': "{clean_value}"'
            # Si es un número válido con un solo punto, dejarlo como número
            return match.group(0)

        # Buscar valores numéricos después de ":"
        # Capturar solo dígitos, puntos y comas (sin incluir el delimitador siguiente)
        text = re.sub(r':\s*([\d.,]+)', quote_malformed_number, text)

        # Remover trailing commas antes de } o ]
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        # Remover espacios en claves de objetos (ej: "item.name" : -> "item.name":)
        text = re.sub(r'"\s+:', r'":', text)

        # Remover espacios antes de comas
        text = re.sub(r'\s+,', ',', text)

        logger.debug(f"JSON después de limpieza: {text[:300]}")
        return text

    def classify_document(self, text_content: str, db: Session) -> Dict[str, Any]:
        """
        Clasifica un documento comercial usando Phi-4 con prompt de BD

        Args:
            text_content: Contenido de texto extraído del documento
            db: Sesión de base de datos

        Returns:
            Dict con el tipo de documento y confianza de la clasificación
        """
        # Obtener el prompt de clasificación desde la BD
        prompt_template = PromptService.get_classification_prompt(db)

        if not prompt_template:
            # Fallback al prompt por defecto si no hay uno en la BD
            prompt = f"""Analiza el siguiente contenido de documento y clasifícalo en una de estas categorías:
- factura
- orden_compra
- certificado_origen
- especificacion_tecnica
- contrato
- remito
- otro

Contenido del documento:
{text_content[:3000]}

Responde ÚNICAMENTE con un JSON en el siguiente formato:
{{"document_type": "tipo_de_documento", "confidence": 0.95, "reasoning": "breve explicación"}}
"""
        else:
            # Usar el prompt de la BD
            variables = {
                "text_content": text_content[:3000]
            }
            prompt = PromptService.render_prompt(
                prompt_template.prompt_template,
                variables,
                response_format=prompt_template.response_format or 'text',
                json_schema=prompt_template.json_schema
            )

        logger.info(f"Clasificando documento con el siguiente prompt: {prompt}")
        try:
            logger.info(f"Clasificando documento con modelo {self.model}")
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                }
            )

            response_text = response['response'].strip()
            logger.info(f"Respuesta raw del modelo (primeros 500 chars): {response_text[:500]}")

            # Intentar extraer JSON de la respuesta
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
                logger.info("JSON extraído de bloque ```json")
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
                logger.info("JSON extraído de bloque ```")

            logger.info(f"Texto a parsear como JSON: {response_text[:500]}")

            if not response_text:
                logger.error("El texto de respuesta está vacío después de extraer JSON")
                return {
                    "error": "Expecting value: line 1 column 1 (char 0)",
                    "classification_reasoning": "La respuesta del modelo estaba vacía"
                }

            # Limpiar JSON antes de parsear
            cleaned_text = self.clean_json_response(response_text)
            logger.info(f"JSON limpio (primeros 500 chars): {cleaned_text[:500]}")

            result = json.loads(cleaned_text)
            logger.info(f"Clasificación exitosa: {result.get('document_type', 'unknown')}")
            return result

        except json.JSONDecodeError as e:
            logger.exception(f"Error de JSON decode: {str(e)}")
            logger.error(f"Texto original que causó el error: {response_text}")
            logger.error(f"Texto limpio que causó el error: {cleaned_text}")
            # Mostrar bytes para detectar caracteres invisibles
            logger.error(f"Bytes del texto limpio: {cleaned_text.encode('unicode_escape').decode('ascii')}")
            raise ValueError(f"No se pudo parsear la respuesta del modelo como JSON: {str(e)}")
        except Exception as e:
            logger.exception(f"Error general en clasificación: {str(e)}")
            raise

    def extract_structured_data(self, text_content: str, document_type: str, db: Session) -> Dict[str, Any]:
        """
        Extrae datos estructurados del documento según su tipo usando prompt de BD

        Args:
            text_content: Contenido de texto del documento
            document_type: Tipo de documento clasificado
            db: Sesión de base de datos

        Returns:
            Dict con los datos extraídos
        """
        # Obtener el prompt de extracción específico para este tipo de documento
        prompt_template = PromptService.get_extraction_prompt(db, document_type)
        logger.info(f"template de prompt obtenido para extracción {document_type}, prompt_tempate: {prompt_template}", )

        if not prompt_template:
            # Fallback a campos por defecto si no hay prompt en la BD
            fields_by_type = {
                "factura": ["numero_factura", "fecha", "proveedor", "cliente", "monto_total", "moneda", "items"],
                "orden_compra": ["numero_orden", "fecha", "proveedor", "cliente", "items", "monto_total"],
                "certificado_origen": ["numero_certificado", "fecha", "pais_origen", "producto", "exportador"],
                "especificacion_tecnica": ["producto", "modelo", "especificaciones", "normas"],
                "contrato": ["numero_contrato", "fecha", "partes", "objeto", "monto"],
                "remito": ["numero_remito", "fecha", "origen", "destino", "items"]
            }

            fields = fields_by_type.get(document_type, ["fecha", "numero_documento", "emisor", "receptor"])

            prompt = f"""Extrae la siguiente información del documento de tipo "{document_type}":

                            Campos a extraer: {', '.join(fields)}

                            Contenido del documento:
                            {text_content[:4000]}

                            Responde ÚNICAMENTE con un JSON con los campos encontrados. Si un campo no está presente, usa null.
                            Formato de respuesta:
                            {{
                            "campo1": "valor1",
                            "campo2": "valor2",
                            ...
                            }}
                        """
        else:
            # Usar el prompt de la BD
            variables = {
                "text_content": text_content[:4000],
                "document_type": document_type
            }
            prompt = PromptService.render_prompt(
                prompt_template.prompt_template,
                variables,
                response_format=prompt_template.response_format or 'text',
                json_schema=prompt_template.json_schema
            )

        try:
            logger.info(f"Extrayendo datos estructurados para documento tipo: {document_type}")
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.2,
                    "top_p": 0.9,
                }
            )

            response_text = response['response'].strip()
            logger.info(f"Respuesta raw extracción (primeros 500 chars): {response_text}")

            # Extraer JSON
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
                logger.info("JSON extraído de bloque ```json")
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
                logger.info("JSON extraído de bloque ```")

            logger.info(f"Texto a parsear como JSON: {response_text[:500]}")

            if not response_text:
                logger.error("El texto de respuesta está vacío después de extraer JSON")
                raise ValueError("La respuesta del modelo estaba vacía")

            # Limpiar JSON antes de parsear
            cleaned_text = self.clean_json_response(response_text)
            logger.info(f"JSON limpio (primeros 500 chars): {cleaned_text[:500]}")

            extracted_data = json.loads(cleaned_text)
            logger.info(f"Extracción exitosa: {len(extracted_data)} campos extraídos")
            return extracted_data

        except json.JSONDecodeError as e:
            logger.exception(f"Error de JSON decode en extracción: {str(e)}")
            logger.error(f"Texto original que causó el error: {response_text}")
            logger.error(f"Texto limpio que causó el error: {cleaned_text}")
            logger.error(f"Bytes del texto limpio: {cleaned_text.encode('unicode_escape').decode('ascii')}")
            raise ValueError(f"No se pudo parsear la respuesta del modelo como JSON: {str(e)}")
        except Exception as e:
            logger.exception(f"Error general en extracción de datos: {str(e)}")
            raise


llama_service = LlamaService()
