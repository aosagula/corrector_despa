"""
Servicio para convertir páginas de PDF a imágenes
"""
from pathlib import Path
from typing import List, Tuple
import logging
from pdf2image import convert_from_path
from PIL import Image
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
    def pdf_to_bw_images(pdf_path: str, dpi: int = 300) -> List[Tuple[bytes, int, int]]:
        """
        Convierte un PDF a imágenes en blanco y negro de alta calidad para documentos provisorios

        Args:
            pdf_path: Ruta al archivo PDF
            dpi: Resolución (default 300 para calidad A4)

        Returns:
            Lista de tuplas (bytes_imagen, ancho, alto) en formato PNG B&N
        """
        try:
            logger.info(f"Convirtiendo PDF a imágenes B&N 300 DPI: {pdf_path}")

            # Convertir PDF a imágenes PIL en alta resolución
            images = convert_from_path(pdf_path, dpi=dpi)

            logger.info(f"PDF convertido a {len(images)} páginas")

            # Convertir cada imagen a B&N y guardar como bytes
            result_list = []
            for i, image in enumerate(images):
                # Convertir a escala de grises
                grayscale_image = image.convert('L')

                # Convertir a blanco y negro puro (1-bit)
                bw_image = grayscale_image.convert('1')

                # Guardar como PNG
                img_byte_arr = BytesIO()
                bw_image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()

                # Obtener dimensiones
                width, height = bw_image.size

                result_list.append((img_bytes, width, height))
                logger.debug(f"Página {i+1}: {width}x{height}px, {len(img_bytes)} bytes")

            return result_list

        except Exception as e:
            logger.exception(f"Error convirtiendo PDF a imágenes B&N: {str(e)}")
            raise ValueError(f"No se pudo convertir el PDF a imágenes B&N: {str(e)}")

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
