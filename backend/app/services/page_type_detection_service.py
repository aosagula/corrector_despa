import re
import logging
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from io import BytesIO
import numpy as np
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ..models.document import PageType, PageTypeDetectionRule, ProvisionalDocumentImage

logger = logging.getLogger(__name__)


class PageTypeDetectionService:
    """Servicio para detectar el tipo de página usando reglas de detección OCR"""

    def __init__(self, db: Session):
        self.db = db

    def detect_page_type(self, image_data: bytes, image_width: int, image_height: int) -> Optional[Tuple[PageType, List[dict]]]:
        """
        Detecta el tipo de página analizando la imagen con las reglas de detección

        Returns:
            Tupla de (PageType, lista de matches con coordenadas) o None si no se detecta
        """
        logger.info(f"Detectando tipo de página para imagen de {image_width}x{image_height}px")

        # Cargar todos los tipos de página ordenados por prioridad de sus reglas
        page_types = self.db.query(PageType).all()
        logger.info(f"Encontrados {len(page_types)} tipos de página para verificar")

        # Para cada tipo de página, verificar si cumple con las reglas
        for page_type in page_types:
            rules = sorted(page_type.detection_rules, key=lambda r: r.priority, reverse=True)

            if not rules:
                logger.info(f"Tipo '{page_type.name}' no tiene reglas, saltando")
                continue

            logger.info(f"Verificando tipo '{page_type.name}' con {len(rules)} reglas")
            matches = []
            all_rules_match = True

            for rule in rules:
                match_result = self._check_rule(image_data, rule)

                if match_result:
                    matches.append({
                        "rule_id": rule.id,
                        "attribute_name": rule.attribute_name,
                        "x1": rule.x1,
                        "y1": rule.y1,
                        "x2": rule.x2,
                        "y2": rule.y2,
                        "expected_value": rule.expected_value,
                        "found_value": match_result["text"],
                        "match_type": rule.match_type,
                        "confidence": match_result["confidence"]
                    })
                else:
                    logger.debug(f"Tipo '{page_type.name}': regla {rule.id} no coincide, descartando tipo")
                    all_rules_match = False
                    break

            # Si todas las reglas coinciden, retornar este tipo de página
            if all_rules_match and matches:
                logger.info(f"Página detectada como tipo '{page_type.name}' con {len(matches)} reglas coincidentes")
                return (page_type, matches)

        logger.warning("No se pudo detectar el tipo de página (ninguna regla coincidió)")
        return None

    def _check_rule(self, image_data: bytes, rule: PageTypeDetectionRule) -> Optional[dict]:
        """
        Verifica si una regla de detección coincide en la imagen

        Returns:
            Dict con texto encontrado y confianza, o None si no coincide
        """
        try:
            # Cargar imagen desde bytes (B&W 1-bit desde base de datos)
            image = Image.open(BytesIO(image_data))

            # Si la imagen es B&W (modo '1'), convertir a grayscale para mejor OCR
            if image.mode == '1':
                image = image.convert('L')

            # Extraer región de interés
            roi = image.crop((rule.x1, rule.y1, rule.x2, rule.y2))

            # Aplicar preprocesamiento para mejorar OCR
            #roi = self._preprocess_for_ocr(roi)

            # Realizar OCR en la región con configuración optimizada para documentos
            # --psm 6: Asume un bloque uniforme de texto
            # --oem 3: Usa el mejor motor OCR disponible (LSTM + legacy)
            # -c tessedit_char_whitelist: Incluye asteriscos y caracteres comunes
            text = pytesseract.image_to_string(
                roi,
                config='--psm 6 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNÑOPQRSTUVWXYZabcdefghijklmnñopqrstuvwxyz0123456789áéíóúÁÉÍÓÚ .,;:()/-*',
                lang='spa'
            ).strip()

            # Post-procesamiento: detectar patrones que parecen asteriscos
            text = self._postprocess_asterisks(text)

            logger.info(f"Rule {rule.id} ({rule.attribute_name}): OCR extrajo '{text}'")

            # Si no hay valor esperado, cualquier texto es válido
            if not rule.expected_value:
                if text:
                    logger.info(f"Rule {rule.id}: Sin valor esperado, texto encontrado: '{text}'")
                    return {"text": text, "confidence": 1.0}
                logger.info(f"Rule {rule.id}: Sin valor esperado, no se encontró texto")
                return None

            # Verificar coincidencia según el tipo de dato
            data_type = rule.data_type or "text"
            comparator = rule.comparator or rule.match_type or "contains"

            matches = False

            if data_type == "text":
                matches = self._compare_text(text, rule.expected_value, comparator)
            elif data_type == "number":
                matches = self._compare_number(text, rule.expected_value, comparator)
            elif data_type == "date":
                matches = self._compare_date(text, rule.expected_value, comparator, rule.date_format)

            logger.info(f"Rule {rule.id}: Tipo={data_type}, Comparador={comparator}, Esperado='{rule.expected_value}', Encontrado='{text}', Match={matches}")

            if matches:
                return {"text": text, "confidence": 0.9}

            return None

        except Exception as e:
            logger.error(f"Error checking rule {rule.id}: {str(e)}", exc_info=True)
            return None

    def detect_document_pages(self, document_id: int) -> List[dict]:
        """
        Detecta el tipo de todas las páginas de un documento provisorio

        Returns:
            Lista de dicts con información de detección por página
        """
        images = self.db.query(ProvisionalDocumentImage).filter(
            ProvisionalDocumentImage.provisional_document_id == document_id
        ).order_by(ProvisionalDocumentImage.page_number).all()

        results = []
        for img in images:
            detection = self.detect_page_type(img.image_data, img.width, img.height)

            if detection:
                page_type, matches = detection
                results.append({
                    "page_number": img.page_number,
                    "page_type_id": page_type.id,
                    "page_type_name": page_type.name,
                    "page_type_display_name": page_type.display_name,
                    "page_type_color": page_type.color,
                    "detection_boxes": matches,
                    "confidence": sum(m["confidence"] for m in matches) / len(matches) if matches else 0
                })
            else:
                results.append({
                    "page_number": img.page_number,
                    "page_type_id": None,
                    "page_type_name": None,
                    "page_type_display_name": "No detectado",
                    "page_type_color": "#6c757d",
                    "detection_boxes": [],
                    "confidence": 0.0
                })

        return results

    def _preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """
        Aplica preprocesamiento a la imagen para mejorar la calidad del OCR

        Args:
            image: Imagen PIL a preprocesar

        Returns:
            Imagen preprocesada
        """
        try:
            # Aumentar contraste para mejorar la detección de caracteres
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # Aumentar nitidez
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)

            # Aplicar filtro para reducir ruido
            image = image.filter(ImageFilter.MedianFilter(size=3))

            return image
        except Exception as e:
            logger.warning(f"Error en preprocesamiento de imagen: {str(e)}")
            return image

    def _postprocess_asterisks(self, text: str) -> str:
        """
        Post-procesa el texto para corregir asteriscos mal reconocidos

        Args:
            text: Texto extraído por OCR

        Returns:
            Texto con asteriscos corregidos
        """
        # Patrones comunes que Tesseract usa para asteriscos
        # A veces los lee como letras repetidas o caracteres extraños
        patterns = [
            (r'[ARERE]{3,}', '*****'),  # ARRERERE -> *****
            (r'[aArReE]{3,}', '*****'),  # arrerere -> *****
            (r'[xX]{3,}', '*****'),      # xxxxx -> *****
            (r'[oO]{3,}', '*****'),      # ooooo -> *****
            (r'[+]{3,}', '*****'),       # +++++ -> *****
        ]

        for pattern, replacement in patterns:
            if re.search(pattern, text):
                logger.debug(f"Corrigiendo patrón '{pattern}' -> '{replacement}' en texto: '{text}'")
                text = re.sub(pattern, replacement, text)

        return text

    def _compare_text(self, text: str, expected: str, comparator: str) -> bool:
        """
        Compara texto según el comparador especificado

        Args:
            text: Texto extraído
            expected: Valor esperado
            comparator: Tipo de comparación

        Returns:
            True si coincide, False si no
        """
        text_upper = text.upper()
        expected_upper = expected.upper()

        if comparator == "contains":
            return expected_upper in text_upper
        elif comparator == "not_contains":
            return expected_upper not in text_upper
        elif comparator == "exact":
            return text_upper == expected_upper
        elif comparator == "not_exact":
            return text_upper != expected_upper
        elif comparator == "regex":
            return bool(re.search(expected, text, re.IGNORECASE))
        else:
            logger.warning(f"Comparador de texto desconocido: {comparator}, usando 'contains'")
            return expected_upper in text_upper

    def _compare_number(self, text: str, expected: str, comparator: str) -> bool:
        """
        Compara números según el comparador especificado

        Args:
            text: Texto extraído (será convertido a número)
            expected: Valor esperado (será convertido a número)
            comparator: Tipo de comparación (eq, ne, gt, lt, gte, lte)

        Returns:
            True si coincide, False si no
        """
        try:
            # Limpiar texto: remover espacios, comas, y tomar solo números y punto/coma decimal
            text_clean = re.sub(r'[^\d.,-]', '', text).replace(',', '.')
            if not text_clean:
                return False

            # Convertir a Decimal para precisión
            found_number = Decimal(text_clean)
            expected_number = Decimal(expected.replace(',', '.'))

            if comparator == "eq":
                return found_number == expected_number
            elif comparator == "ne":
                return found_number != expected_number
            elif comparator == "gt":
                return found_number > expected_number
            elif comparator == "lt":
                return found_number < expected_number
            elif comparator == "gte":
                return found_number >= expected_number
            elif comparator == "lte":
                return found_number <= expected_number
            else:
                logger.warning(f"Comparador numérico desconocido: {comparator}, usando 'eq'")
                return found_number == expected_number

        except (ValueError, InvalidOperation) as e:
            logger.warning(f"Error convirtiendo a número: text='{text}', expected='{expected}': {str(e)}")
            return False

    def _compare_date(self, text: str, expected: str, comparator: str, date_format: Optional[str]) -> bool:
        """
        Compara fechas según el comparador especificado

        Args:
            text: Texto extraído (será convertido a fecha)
            expected: Valor esperado (será convertido a fecha)
            comparator: Tipo de comparación (eq, ne, gt, lt, gte, lte)
            date_format: Formato de fecha para parsing (ej: %d/%m/%Y)

        Returns:
            True si coincide, False si no
        """
        if not date_format:
            date_format = "%d/%m/%Y"  # Formato por defecto

        try:
            # Intentar parsear ambas fechas
            found_date = datetime.strptime(text.strip(), date_format)
            expected_date = datetime.strptime(expected.strip(), date_format)

            if comparator == "eq":
                return found_date == expected_date
            elif comparator == "ne":
                return found_date != expected_date
            elif comparator == "gt":
                return found_date > expected_date
            elif comparator == "lt":
                return found_date < expected_date
            elif comparator == "gte":
                return found_date >= expected_date
            elif comparator == "lte":
                return found_date <= expected_date
            else:
                logger.warning(f"Comparador de fecha desconocido: {comparator}, usando 'eq'")
                return found_date == expected_date

        except ValueError as e:
            logger.warning(f"Error parseando fecha: text='{text}', expected='{expected}', format='{date_format}': {str(e)}")
            return False
