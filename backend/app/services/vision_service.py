"""
Servicio para extracción de datos usando modelos de visión multimodal
"""
import ollama
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..core.config import settings
from .prompt_service import PromptService
from .pdf_to_image_service import pdf_to_image_service
import json
import logging
import re

logger = logging.getLogger(__name__)


class VisionService:
    """Servicio para extraer datos usando modelos multimodales de visión"""

    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.vision_model = settings.VISION_MODEL

    def clean_json_response(self, text: str) -> str:
        """
        Limpia y corrige problemas comunes en JSON generado por LLM
        (Reutiliza la lógica de LlamaService)
        """
        # Remover texto antes/después del JSON
        text = text.strip()

        # Reemplazar comillas tipográficas por comillas normales
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")

        # Remover caracteres de control invisibles (excepto \n, \r, \t)
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

        # Normalizar espacios en blanco
        text = re.sub(r'[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]', ' ', text)

        # Remover comentarios de JavaScript/C++ (// comentario)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
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
        def quote_malformed_number(match):
            value = match.group(1)
            if (',' in value and not value.endswith(',')) or value.count('.') > 1:
                clean_value = value.rstrip(',')
                return f': "{clean_value}"'
            return match.group(0)

        text = re.sub(r':\s*([\d.,]+)', quote_malformed_number, text)

        # Remover trailing commas antes de } o ]
        text = re.sub(r',(\s*[}\]])', r'\1', text)

        # Remover espacios en claves de objetos
        text = re.sub(r'"\s+:', r'":', text)

        # Remover espacios antes de comas
        text = re.sub(r'\s+,', ',', text)

        logger.debug(f"JSON después de limpieza: {text[:300]}")
        return text

    def extract_from_images(
        self,
        image_bytes_list: List[bytes],
        document_type: str,
        db: Session
    ) -> tuple[Dict[str, Any], str]:
        """
        Extrae datos estructurados usando el modelo de visión

        Args:
            image_bytes_list: Lista de imágenes del documento (una por página)
            document_type: Tipo de documento para seleccionar el prompt apropiado
            db: Sesión de base de datos

        Returns:
            Tupla con (diccionario de datos extraídos, prompt usado)
        """
        try:
            # Obtener el prompt de extracción desde la BD
            prompt_template = PromptService.get_extraction_prompt(document_type, db)

            if not prompt_template:
                raise ValueError(f"No hay prompt de extracción configurado para {document_type}")

            # Para vision, no necesitamos pasar text_content
            # El prompt debe estar diseñado para análisis de imagen
            variables = {
                "document_type": document_type
            }

            prompt = PromptService.render_prompt(
                prompt_template.prompt_template,
                variables,
                response_format=prompt_template.response_format or 'json',
                json_schema=prompt_template.json_schema
            )

            logger.info(f"Extrayendo datos con modelo de visión {self.vision_model}")
            logger.info(f"Procesando {len(image_bytes_list)} páginas")

            # Convertir imágenes a base64
            images_base64 = pdf_to_image_service.images_to_base64_list(image_bytes_list)

            # Llamar al modelo de visión con todas las imágenes
            response = self.client.generate(
                model=self.vision_model,
                prompt=prompt,
                images=images_base64,
                options={
                    "temperature": 0.2,
                    "top_p": 0.9,
                }
            )

            response_text = response['response'].strip()
            logger.info(f"Respuesta raw del modelo de visión (primeros 500 chars): {response_text[:500]}")

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

            if not response_text:
                logger.error("El texto de respuesta está vacío después de extraer JSON")
                raise ValueError("La respuesta del modelo estaba vacía")

            # Limpiar JSON antes de parsear
            cleaned_text = self.clean_json_response(response_text)
            logger.info(f"JSON limpio (primeros 500 chars): {cleaned_text[:500]}")

            extracted_data = json.loads(cleaned_text)
            logger.info(f"Extracción exitosa usando visión: {len(extracted_data)} campos extraídos")
            return extracted_data, prompt

        except json.JSONDecodeError as e:
            logger.exception(f"Error de JSON decode en extracción con visión: {str(e)}")
            logger.error(f"Texto original que causó el error: {response_text}")
            logger.error(f"Texto limpio que causó el error: {cleaned_text}")
            raise ValueError(f"No se pudo parsear la respuesta del modelo como JSON: {str(e)}")
        except Exception as e:
            logger.exception(f"Error general en extracción con visión: {str(e)}")
            raise

    def extract_from_pdf(
        self,
        pdf_path: str,
        document_type: str,
        db: Session,
        dpi: int = 200
    ) -> tuple[Dict[str, Any], str]:
        """
        Extrae datos de un PDF convirtiéndolo a imágenes primero

        Args:
            pdf_path: Ruta al archivo PDF
            document_type: Tipo de documento
            db: Sesión de base de datos
            dpi: Resolución para la conversión de PDF a imagen

        Returns:
            Tupla con (diccionario de datos extraídos, prompt usado)
        """
        logger.info(f"Extrayendo datos de PDF usando visión: {pdf_path}")

        # Convertir PDF a imágenes
        image_bytes_list = pdf_to_image_service.pdf_to_images(pdf_path, dpi=dpi)

        # Extraer datos de las imágenes
        return self.extract_from_images(image_bytes_list, document_type, db)

    def extract_from_image_file(
        self,
        image_path: str,
        document_type: str,
        db: Session
    ) -> tuple[Dict[str, Any], str]:
        """
        Extrae datos de un archivo de imagen (PNG, JPG, etc.)

        Args:
            image_path: Ruta al archivo de imagen
            document_type: Tipo de documento
            db: Sesión de base de datos

        Returns:
            Tupla con (diccionario de datos extraídos, prompt usado)
        """
        logger.info(f"Extrayendo datos de imagen usando visión: {image_path}")

        # Leer imagen como bytes
        with open(image_path, 'rb') as f:
            image_bytes = f.read()

        # Extraer datos de la imagen
        return self.extract_from_images([image_bytes], document_type, db)


vision_service = VisionService()
