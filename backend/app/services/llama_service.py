import ollama
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..core.config import settings
from .prompt_service import PromptService
import json


class LlamaService:
    """Servicio para interactuar con el modelo Phi-4 a través de Ollama"""

    def __init__(self):
        self.client = ollama.Client(host=settings.OLLAMA_HOST)
        self.model = settings.OLLAMA_MODEL

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
            # Usar el prompt de la BD
            variables = {
                "text_content": text_content[:3000]
            }
            prompt = PromptService.render_prompt(prompt_template.prompt_template, variables)

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

    def extract_structured_data(self, text_content: str, document_type: str, db: Session) -> Dict[str, Any]:
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
            prompt = PromptService.render_prompt(prompt_template.prompt_template, variables)

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
