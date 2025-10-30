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

        # Buscar el inicio del JSON (primer { o [)
        json_start = min(
            text.find('{') if text.find('{') != -1 else len(text),
            text.find('[') if text.find('[') != -1 else len(text)
        )
        if json_start < len(text):
            text = text[json_start:]

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

        # Escapar comillas dobles dentro de valores de string JSON
        # Procesar línea por línea para evitar falsos positivos
        def fix_json_quotes_in_line(line: str) -> str:
            # Buscar patrón: "key": "value..."
            # Contar comillas para detectar si hay comillas internas
            match = re.match(r'^(\s*)"([^"]+)":\s*"(.*)$', line)
            if not match:
                return line

            indent = match.group(1)
            key = match.group(2)
            rest = match.group(3)

            # Contar comillas en el resto de la línea
            quote_count = rest.count('"')

            # Si hay más de 1 comilla (la de cierre + otras internas)
            if quote_count > 1:
                # Buscar la última comilla (la de cierre del valor)
                last_quote_idx = rest.rfind('"')
                if last_quote_idx > 0:
                    # Dividir en: valor_interno + comilla_cierre + resto (coma, etc)
                    value_part = rest[:last_quote_idx]
                    closing_part = rest[last_quote_idx:]

                    # Escapar comillas en la parte del valor
                    value_escaped = value_part.replace('"', '\\"')

                    return f'{indent}"{key}": "{value_escaped}{closing_part}'

            return line

        # Aplicar a cada línea
        text_lines = text.split('\n')
        text = '\n'.join(fix_json_quotes_in_line(line) for line in text_lines)

        # Remover expresiones matemáticas/JavaScript (ej: 2000 + (2 * 42) + 1, 1008 + ((2 * 42)))
        # Patrón mejorado que captura cualquier combinación de números, operadores y paréntesis
        # Convertir a string para preservar la intención del LLM
        def convert_math_expression(match):
            expr = match.group(1)
            # Si contiene operadores matemáticos, convertir a string
            if any(op in expr for op in ['+', '-', '*', '/']):
                return f': "{expr}"'
            return match.group(0)

        # Buscar expresiones que contengan números con operadores
        text = re.sub(r':\s*([0-9()\s\+\-\*\/]+(?:[0-9()\s\+\-\*\/]+)?)', convert_math_expression, text)

        # Convertir números con unidades/sufijos a strings (2000L = 2000 Litros, 3.14kg, etc)
        # Preservar el contenido completo incluyendo la unidad
        # 2000L → "2000L", 3.14kg → "3.14kg", 100m → "100m"
        text = re.sub(r':\s*(\d+\.?\d*[a-zA-Z]+)\b', r': "\1"', text)

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

    @staticmethod
    def get_language_instruction() -> str:
        """
        Retorna la instrucción de idioma según la configuración

        Returns:
            String con la instrucción de idioma para el LLM
        """
        language_map = {
            "es": "Responde en español.",
            "en": "Respond in English.",
            "pt": "Responda em português.",
            "fr": "Répondez en français.",
            "de": "Antworten Sie auf Deutsch.",
            "it": "Rispondi in italiano."
        }

        lang = settings.RESPONSE_LANGUAGE.lower()
        return language_map.get(lang, language_map["es"])

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
            language_instruction = self.get_language_instruction()
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

{language_instruction}
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

            # Intentar recuperación
            try:
                error_pos = e.pos if hasattr(e, 'pos') else len(cleaned_text)

                # Intentar cerrar el JSON en la posición del error
                truncated = cleaned_text[:error_pos].rstrip()
                open_braces = truncated.count('{')
                close_braces = truncated.count('}')
                truncated = truncated.rstrip(',')
                truncated += '\n' + ('}' * (open_braces - close_braces))

                logger.info(f"Intentando parsear JSON truncado: {truncated[:500]}")
                result = json.loads(truncated)
                logger.warning(f"JSON reparado exitosamente truncando en posición {error_pos}")
                return result

            except Exception as recovery_error:
                logger.error(f"Falló la recuperación del JSON: {str(recovery_error)}")
                logger.error(f"Bytes del texto limpio: {cleaned_text.encode('unicode_escape').decode('ascii')}")
                raise ValueError(f"No se pudo parsear la respuesta del modelo como JSON: {str(e)}")
        except Exception as e:
            logger.exception(f"Error general en clasificación: {str(e)}")
            raise

    def extract_structured_data(self, text_content: str, document_type: str, db: Session) -> tuple[Dict[str, Any], str]:
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
        logger.info(f"template de prompt obtenido para extracción {document_type}, prompt_tempate: {prompt_template.prompt_template}", )

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

        logger.info(f"Extrayendo datos estructurados con el siguiente prompt: {prompt}")
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
            return extracted_data, prompt

        except json.JSONDecodeError as e:
            logger.exception(f"Error de JSON decode en extracción: {str(e)}")
            logger.error(f"Texto original que causó el error: {response_text}")
            logger.error(f"Texto limpio que causó el error: {cleaned_text}")

            # Intentar recuperación: extraer hasta donde sea válido
            try:
                # Encontrar la posición del error
                error_pos = e.pos if hasattr(e, 'pos') else len(cleaned_text)

                # Intentar diferentes estrategias de reparación
                # 1. Remover el campo "reasoning" si existe (suele estar al final)
                if '"reasoning"' in cleaned_text:
                    # Buscar y remover el campo reasoning
                    reasoning_pattern = r',?\s*"reasoning"\s*:\s*"[^"]*"?\s*'
                    repaired_text = re.sub(reasoning_pattern, '', cleaned_text)
                    # Asegurar que el JSON cierre correctamente
                    if not repaired_text.rstrip().endswith('}'):
                        repaired_text = repaired_text.rstrip().rstrip(',') + '\n}'

                    logger.info(f"Intentando parsear JSON sin campo 'reasoning': {repaired_text[:500]}")
                    extracted_data = json.loads(repaired_text)
                    logger.warning(f"JSON reparado exitosamente removiendo campo 'reasoning'")
                    return extracted_data, prompt

                # 2. Intentar cerrar el JSON en la posición del error
                truncated = cleaned_text[:error_pos].rstrip()
                # Contar llaves abiertas vs cerradas
                open_braces = truncated.count('{')
                close_braces = truncated.count('}')
                # Remover trailing comma si existe
                truncated = truncated.rstrip(',')
                # Agregar llaves de cierre faltantes
                truncated += '\n' + ('}' * (open_braces - close_braces))

                logger.info(f"Intentando parsear JSON truncado: {truncated[:500]}")
                extracted_data = json.loads(truncated)
                logger.warning(f"JSON reparado exitosamente truncando en posición {error_pos}")
                return extracted_data, prompt

            except Exception as recovery_error:
                logger.error(f"Falló la recuperación del JSON: {str(recovery_error)}")
                logger.error(f"Bytes del texto limpio: {cleaned_text.encode('unicode_escape').decode('ascii')}")
                raise ValueError(f"No se pudo parsear la respuesta del modelo como JSON: {str(e)}")
        except Exception as e:
            logger.exception(f"Error general en extracción de datos: {str(e)}")
            raise


llama_service = LlamaService()
