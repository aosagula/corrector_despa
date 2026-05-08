import io
import ollama
from typing import Dict, Any, List
from PIL import Image
from sqlalchemy.orm import Session
from ..core.config import settings
from .prompt_service import PromptService
import json


class LlamaService:
    """Servicio para interactuar con modelos LLM a través de Ollama (texto o multimodal)"""

    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _images_to_bytes(self, images: List[Image.Image]) -> List[bytes]:
        result = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            result.append(buf.getvalue())
        return result

    def _parse_json_response(self, response_text: str) -> dict:
        text = response_text.strip()
        if '```json' in text:
            start = text.find('```json') + 7
            end = text.find('```', start)
            text = text[start:end].strip()
        elif '```' in text:
            start = text.find('```') + 3
            end = text.find('```', start)
            text = text[start:end].strip()
        return json.loads(text)

    # ------------------------------------------------------------------
    # Pipeline de texto (Phi-4 / modelos sin visión)
    # ------------------------------------------------------------------

    def classify_document(self, text_content: str, db: Session) -> Dict[str, Any]:
        prompt_template = PromptService.get_classification_prompt(db)

        if not prompt_template:
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
            variables = {"text_content": text_content[:3000]}
            prompt = PromptService.render_prompt(prompt_template.prompt_template, variables)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.3, "top_p": 0.9}
            )
            return self._parse_json_response(response['response'])
        except Exception as e:
            print(f"Error en clasificación: {str(e)}")
            return {"document_type": "desconocido", "confidence": 0.0, "reasoning": f"Error: {str(e)}"}

    def extract_structured_data(self, text_content: str, document_type: str, db: Session) -> Dict[str, Any]:
        prompt_template = PromptService.get_extraction_prompt(db, document_type)

        if not prompt_template:
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
            variables = {"text_content": text_content[:4000], "document_type": document_type}
            prompt = PromptService.render_prompt(prompt_template.prompt_template, variables)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={"temperature": 0.2, "top_p": 0.9}
            )
            return self._parse_json_response(response['response'])
        except Exception as e:
            print(f"Error en extracción de datos: {str(e)}")
            return {"error": str(e)}

    # ------------------------------------------------------------------
    # Pipeline multimodal (Gemma / modelos con visión)
    # Las imágenes se pasan directamente al modelo; no se requiere Tesseract.
    # ------------------------------------------------------------------

    def classify_document_multimodal(self, images: List[Image.Image], db: Session) -> Dict[str, Any]:
        """Clasifica un documento pasando sus imágenes directamente al modelo multimodal."""
        prompt_template = PromptService.get_classification_prompt(db)

        if not prompt_template:
            prompt = """Analiza las imágenes del documento y clasifícalo en una de estas categorías:
- factura
- orden_compra
- certificado_origen
- especificacion_tecnica
- contrato
- remito
- otro

Responde ÚNICAMENTE con un JSON en el siguiente formato:
{"document_type": "tipo_de_documento", "confidence": 0.95, "reasoning": "breve explicación"}
"""
        else:
            # Para multimodal el placeholder {text_content} se reemplaza con instrucción de visión
            variables = {"text_content": "[contenido visual del documento adjunto]"}
            prompt = PromptService.render_prompt(prompt_template.prompt_template, variables)

        # Solo primeras 2 páginas para clasificación (reduce tokens/tiempo)
        image_bytes = self._images_to_bytes(images[:2])

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                images=image_bytes,
                options={"temperature": 0.3, "top_p": 0.9}
            )
            return self._parse_json_response(response['response'])
        except Exception as e:
            print(f"Error en clasificación multimodal: {str(e)}")
            return {"document_type": "desconocido", "confidence": 0.0, "reasoning": f"Error: {str(e)}"}

    def extract_structured_data_multimodal(
        self, images: List[Image.Image], document_type: str, db: Session
    ) -> Dict[str, Any]:
        """Extrae datos estructurados pasando las imágenes directamente al modelo multimodal."""
        prompt_template = PromptService.get_extraction_prompt(db, document_type)

        if not prompt_template:
            fields_by_type = {
                "factura": ["numero_factura", "fecha", "proveedor", "cliente", "monto_total", "moneda", "items"],
                "orden_compra": ["numero_orden", "fecha", "proveedor", "cliente", "items", "monto_total"],
                "certificado_origen": ["numero_certificado", "fecha", "pais_origen", "producto", "exportador"],
                "especificacion_tecnica": ["producto", "modelo", "especificaciones", "normas"],
                "contrato": ["numero_contrato", "fecha", "partes", "objeto", "monto"],
                "remito": ["numero_remito", "fecha", "origen", "destino", "items"]
            }
            fields = fields_by_type.get(document_type, ["fecha", "numero_documento", "emisor", "receptor"])
            prompt = f"""Analiza las imágenes del documento de tipo "{document_type}" y extrae los siguientes campos:

Campos a extraer: {', '.join(fields)}

Responde ÚNICAMENTE con un JSON con los campos encontrados. Si un campo no está presente, usa null.
Formato de respuesta:
{{
  "campo1": "valor1",
  "campo2": "valor2",
  ...
}}
"""
        else:
            variables = {
                "text_content": "[contenido visual del documento adjunto]",
                "document_type": document_type
            }
            prompt = PromptService.render_prompt(prompt_template.prompt_template, variables)

        # Todas las páginas para extracción completa
        image_bytes = self._images_to_bytes(images)

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                images=image_bytes,
                options={"temperature": 0.2, "top_p": 0.9}
            )
            return self._parse_json_response(response['response'])
        except Exception as e:
            print(f"Error en extracción multimodal: {str(e)}")
            return {"error": str(e)}


llama_service = LlamaService()
