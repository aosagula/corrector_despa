"""
Servicio para extraer datos usando coordenadas específicas en imágenes
"""
from typing import Dict, List
import logging
from PIL import Image
from io import BytesIO
import pytesseract

logger = logging.getLogger(__name__)


class CoordinateExtractionService:
    """Servicio para extraer texto de regiones específicas de imágenes usando coordenadas"""

    @staticmethod
    def _get_tesseract_config(data_type: str) -> str:
        """
        Obtiene la configuración de Tesseract según el tipo de dato

        Args:
            data_type: Tipo de dato ('text', 'number', 'date')

        Returns:
            String de configuración para Tesseract
        """
        configs = {
            'number': '--psm 7 -c tessedit_char_whitelist=0123456789.,- outputbase digits',
            'date': '--psm 7 -c tessedit_char_whitelist=0123456789/-',
            'text': '--psm 6'  # Asume un bloque de texto uniforme
        }
        return configs.get(data_type, '--psm 6')

    @staticmethod
    def extract_from_coordinates(
        image_bytes: bytes,
        coordinates: List[Dict]
    ) -> Dict[str, str]:
        """
        Extrae texto de regiones específicas de una imagen usando coordenadas

        Args:
            image_bytes: Bytes de la imagen
            coordinates: Lista de diccionarios con formato:
                {
                    'label': 'nombre_atributo',
                    'data_type': 'text|number|date',  # Opcional
                    'x1': int,
                    'y1': int,
                    'x2': int,
                    'y2': int
                }

        Returns:
            Diccionario con label como clave y texto extraído como valor
        """
        try:
            # Cargar imagen desde bytes
            image = Image.open(BytesIO(image_bytes))

            results = {}

            for coord in coordinates:
                label = coord['label']
                data_type = coord.get('data_type', 'text')
                x1, y1, x2, y2 = coord['x1'], coord['y1'], coord['x2'], coord['y2']

                # Validar coordenadas
                if x2 <= x1 or y2 <= y1:
                    logger.warning(f"Coordenadas inválidas para {label}: ({x1},{y1}) -> ({x2},{y2})")
                    results[label] = ""
                    continue

                # Recortar región de interés
                roi = image.crop((x1, y1, x2, y2))

                # Obtener configuración de Tesseract según tipo de dato
                tesseract_config = CoordinateExtractionService._get_tesseract_config(data_type)

                # Extraer texto usando Tesseract con configuración específica
                text = pytesseract.image_to_string(roi, lang='spa', config=tesseract_config).strip()

                results[label] = text
                logger.debug(f"Extraído '{label}' (tipo: {data_type}): {text[:50]}...")

            return results

        except Exception as e:
            logger.exception(f"Error extrayendo datos por coordenadas: {str(e)}")
            raise ValueError(f"Error en extracción por coordenadas: {str(e)}")

    @staticmethod
    def extract_from_document_images(
        images_data: List[tuple],  # Lista de (bytes, width, height)
        coordinates_by_page: Dict[int, List[Dict]]  # {page_number: [coordinates]}
    ) -> Dict[str, str]:
        """
        Extrae datos de múltiples páginas de un documento

        Args:
            images_data: Lista de tuplas (image_bytes, width, height)
            coordinates_by_page: Diccionario con coordenadas agrupadas por número de página

        Returns:
            Diccionario con todos los datos extraídos
        """
        all_results = {}

        for page_num, (img_bytes, width, height) in enumerate(images_data, start=1):
            if page_num not in coordinates_by_page:
                logger.debug(f"No hay coordenadas definidas para la página {page_num}")
                continue

            coords = coordinates_by_page[page_num]
            page_results = CoordinateExtractionService.extract_from_coordinates(
                img_bytes,
                coords
            )

            # Mergear resultados, agregando sufijo si hay duplicados
            for label, value in page_results.items():
                if label in all_results:
                    # Si ya existe, agregar sufijo con número de página
                    all_results[f"{label}_p{page_num}"] = value
                else:
                    all_results[label] = value

        return all_results


coordinate_extraction_service = CoordinateExtractionService()
