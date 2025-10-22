import ollama
from typing import Dict, Any, Optional
from ..core.config import settings
import json


class LlamaService:
    """Servicio para interactuar con el modelo Phi-4 a través de Ollama"""

    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL

    def classify_document(self, text_content: str) -> Dict[str, Any]:
        """
        Clasifica un documento comercial usando Phi-4

        Args:
            text_content: Contenido de texto extraído del documento

        Returns:
            Dict con el tipo de documento y confianza de la clasificación
        """
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

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.3,
                    "top_p": 0.9,
                }
            )

            response_text = response['response'].strip()

            # Intentar extraer JSON de la respuesta
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()

            result = json.loads(response_text)
            return result

        except Exception as e:
            print(f"Error en clasificación: {str(e)}")
            return {
                "document_type": "desconocido",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }

    def extract_structured_data(self, text_content: str, document_type: str) -> Dict[str, Any]:
        """
        Extrae datos estructurados del documento según su tipo

        Args:
            text_content: Contenido de texto del documento
            document_type: Tipo de documento clasificado

        Returns:
            Dict con los datos extraídos
        """
        # Definir campos según tipo de documento
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

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.2,
                    "top_p": 0.9,
                }
            )

            response_text = response['response'].strip()

            # Extraer JSON
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()

            extracted_data = json.loads(response_text)
            return extracted_data

        except Exception as e:
            print(f"Error en extracción de datos: {str(e)}")
            return {"error": str(e)}


llama_service = LlamaService()
