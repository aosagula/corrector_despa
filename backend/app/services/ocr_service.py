import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import PyPDF2
from typing import Optional, List
import os
import tempfile


class OCRService:
    """Servicio para extraer texto de PDFs e imágenes"""

    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extrae texto de un archivo PDF

        Args:
            file_path: Ruta al archivo PDF

        Returns:
            Texto extraído del PDF
        """
        text_content = ""

        try:
            # Intentar extraer texto directamente del PDF
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"

            # Si no se extrajo mucho texto, probablemente sea un PDF con imágenes
            if len(text_content.strip()) < 100:
                text_content = self._extract_text_from_pdf_images(file_path)

        except Exception as e:
            print(f"Error extrayendo texto de PDF: {str(e)}")
            # Intentar con OCR si falla la extracción directa
            text_content = self._extract_text_from_pdf_images(file_path)

        return text_content.strip()

    def _extract_text_from_pdf_images(self, file_path: str) -> str:
        """
        Extrae texto de un PDF usando OCR en las imágenes de cada página

        Args:
            file_path: Ruta al archivo PDF

        Returns:
            Texto extraído mediante OCR
        """
        text_content = ""

        try:
            # Convertir PDF a imágenes
            images = convert_from_path(file_path, dpi=300)

            # Aplicar OCR a cada imagen
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang='spa+eng')
                text_content += f"\n--- Página {i+1} ---\n{page_text}\n"

        except Exception as e:
            print(f"Error en OCR de PDF: {str(e)}")

        return text_content

    def extract_text_from_image(self, file_path: str) -> str:
        """
        Extrae texto de una imagen usando OCR

        Args:
            file_path: Ruta al archivo de imagen

        Returns:
            Texto extraído de la imagen
        """
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='spa+eng')
            return text.strip()
        except Exception as e:
            print(f"Error en OCR de imagen: {str(e)}")
            return ""

    def extract_text(self, file_path: str, file_extension: str) -> str:
        """
        Extrae texto de un archivo según su extensión

        Args:
            file_path: Ruta al archivo
            file_extension: Extensión del archivo (.pdf, .png, .jpg, etc.)

        Returns:
            Texto extraído del archivo
        """
        file_extension = file_extension.lower()

        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Extensión de archivo no soportada: {file_extension}")


ocr_service = OCRService()
