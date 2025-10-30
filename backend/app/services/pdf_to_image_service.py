"""
Servicio para convertir páginas de PDF a imágenes
"""
from pathlib import Path
from typing import List
import logging
from pdf2image import convert_from_path
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


class PDFToImageService:
    """Servicio para convertir PDFs a imágenes"""

    @staticmethod
    def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[bytes]:
        """
        Convierte un PDF a una lista de imágenes (una por página)

        Args:
            pdf_path: Ruta al archivo PDF
            dpi: Resolución de las imágenes generadas (mayor = mejor calidad)

        Returns:
            Lista de bytes de imágenes en formato PNG
        """
        try:
            logger.info(f"Convirtiendo PDF a imágenes: {pdf_path} (DPI: {dpi})")

            # Convertir PDF a imágenes PIL
            images = convert_from_path(pdf_path, dpi=dpi)

            logger.info(f"PDF convertido a {len(images)} páginas")

            # Convertir cada imagen PIL a bytes
            image_bytes_list = []
            for i, image in enumerate(images):
                # Guardar imagen en bytes
                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                image_bytes_list.append(img_bytes)
                logger.debug(f"Página {i+1}: {len(img_bytes)} bytes")

            return image_bytes_list

        except Exception as e:
            logger.exception(f"Error convirtiendo PDF a imágenes: {str(e)}")
            raise ValueError(f"No se pudo convertir el PDF a imágenes: {str(e)}")

    @staticmethod
    def image_to_base64(image_bytes: bytes) -> str:
        """
        Convierte bytes de imagen a base64

        Args:
            image_bytes: Bytes de la imagen

        Returns:
            String en base64
        """
        return base64.b64encode(image_bytes).decode('utf-8')

    @staticmethod
    def images_to_base64_list(image_bytes_list: List[bytes]) -> List[str]:
        """
        Convierte lista de bytes de imágenes a lista de base64

        Args:
            image_bytes_list: Lista de bytes de imágenes

        Returns:
            Lista de strings en base64
        """
        return [PDFToImageService.image_to_base64(img_bytes) for img_bytes in image_bytes_list]


pdf_to_image_service = PDFToImageService()
