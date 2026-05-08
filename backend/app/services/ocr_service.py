from PIL import Image
from pdf2image import convert_from_path
from typing import List
import os

try:
    import pytesseract
    import PyPDF2
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class OCRService:
    """Servicio para extraer texto de PDFs e imágenes"""

    def extract_text_from_pdf(self, file_path: str) -> str:
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract / PyPDF2 no disponible. Use modo multimodal.")

        text_content = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"

            if len(text_content.strip()) < 100:
                text_content = self._extract_text_from_pdf_images(file_path)

        except Exception as e:
            print(f"Error extrayendo texto de PDF: {str(e)}")
            text_content = self._extract_text_from_pdf_images(file_path)

        return text_content.strip()

    def _extract_text_from_pdf_images(self, file_path: str) -> str:
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract no disponible. Use modo multimodal.")

        text_content = ""
        try:
            images = convert_from_path(file_path, dpi=300)
            for i, image in enumerate(images):
                page_text = pytesseract.image_to_string(image, lang='spa+eng')
                text_content += f"\n--- Página {i+1} ---\n{page_text}\n"
        except Exception as e:
            print(f"Error en OCR de PDF: {str(e)}")

        return text_content

    def extract_text_from_image(self, file_path: str) -> str:
        if not TESSERACT_AVAILABLE:
            raise RuntimeError("Tesseract no disponible. Use modo multimodal.")

        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='spa+eng')
            return text.strip()
        except Exception as e:
            print(f"Error en OCR de imagen: {str(e)}")
            return ""

    def extract_text(self, file_path: str, file_extension: str) -> str:
        file_extension = file_extension.lower()

        if file_extension == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Extensión de archivo no soportada: {file_extension}")

    def get_images(self, file_path: str, file_extension: str) -> List[Image.Image]:
        """
        Devuelve las páginas/imágenes del documento como objetos PIL.
        Usado por el pipeline multimodal: no invoca Tesseract.
        """
        file_extension = file_extension.lower()

        if file_extension == '.pdf':
            try:
                # dpi 150 es suficiente para visión; reduce memoria vs 300
                return convert_from_path(file_path, dpi=150)
            except Exception as e:
                print(f"Error convirtiendo PDF a imágenes: {str(e)}")
                return []
        elif file_extension in ['.png', '.jpg', '.jpeg']:
            try:
                return [Image.open(file_path)]
            except Exception as e:
                print(f"Error abriendo imagen: {str(e)}")
                return []
        else:
            raise ValueError(f"Extensión de archivo no soportada: {file_extension}")


ocr_service = OCRService()
