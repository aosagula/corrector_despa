from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from ..models.document import PromptTemplate
from ..schemas.document import PromptTemplateCreate, PromptTemplateUpdate


class PromptService:
    """Servicio para gestionar plantillas de prompts"""

    @staticmethod
    def create_prompt(db: Session, prompt_data: PromptTemplateCreate) -> PromptTemplate:
        """Crear una nueva plantilla de prompt"""
        db_prompt = PromptTemplate(**prompt_data.model_dump())
        db.add(db_prompt)
        db.commit()
        db.refresh(db_prompt)
        return db_prompt

    @staticmethod
    def get_prompt_by_id(db: Session, prompt_id: int) -> Optional[PromptTemplate]:
        """Obtener un prompt por ID"""
        return db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()

    @staticmethod
    def get_prompt_by_name(db: Session, name: str) -> Optional[PromptTemplate]:
        """Obtener un prompt por nombre"""
        return db.query(PromptTemplate).filter(PromptTemplate.name == name).first()

    @staticmethod
    def get_all_prompts(db: Session, skip: int = 0, limit: int = 100) -> List[PromptTemplate]:
        """Obtener todos los prompts"""
        return db.query(PromptTemplate).offset(skip).limit(limit).all()

    @staticmethod
    def get_prompts_by_type(db: Session, prompt_type: str, active_only: bool = True) -> List[PromptTemplate]:
        """Obtener prompts por tipo (classification o extraction)"""
        query = db.query(PromptTemplate).filter(PromptTemplate.prompt_type == prompt_type)
        if active_only:
            query = query.filter(PromptTemplate.is_active == 1)
        return query.all()

    @staticmethod
    def get_classification_prompt(db: Session) -> Optional[PromptTemplate]:
        """Obtener el prompt activo de clasificación"""
        return db.query(PromptTemplate).filter(
            PromptTemplate.prompt_type == "classification",
            PromptTemplate.is_active == 1
        ).first()

    @staticmethod
    def get_extraction_prompt(db: Session, document_type: str) -> Optional[PromptTemplate]:
        """Obtener el prompt activo de extracción para un tipo de documento específico"""
        return db.query(PromptTemplate).filter(
            PromptTemplate.prompt_type == "extraction",
            PromptTemplate.document_type == document_type,
            PromptTemplate.is_active == 1
        ).first()

    @staticmethod
    def update_prompt(db: Session, prompt_id: int, prompt_data: PromptTemplateUpdate) -> Optional[PromptTemplate]:
        """Actualizar un prompt existente"""
        db_prompt = PromptService.get_prompt_by_id(db, prompt_id)
        if not db_prompt:
            return None

        update_data = prompt_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_prompt, field, value)

        db.commit()
        db.refresh(db_prompt)
        return db_prompt

    @staticmethod
    def delete_prompt(db: Session, prompt_id: int) -> bool:
        """Eliminar un prompt"""
        db_prompt = PromptService.get_prompt_by_id(db, prompt_id)
        if not db_prompt:
            return False

        db.delete(db_prompt)
        db.commit()
        return True

    @staticmethod
    def render_prompt(prompt_template: str, variables: Dict[str, Any]) -> str:
        """
        Renderiza un template de prompt reemplazando las variables

        Args:
            prompt_template: Template con variables como {text_content}, {document_type}
            variables: Diccionario con los valores de las variables

        Returns:
            Prompt renderizado con las variables reemplazadas
        """
        try:
            return prompt_template.format(**variables)
        except KeyError as e:
            raise ValueError(f"Variable faltante en el template: {e}")

    @staticmethod
    def initialize_default_prompts(db: Session):
        """Inicializar prompts por defecto si no existen"""

        # Verificar si ya existen prompts
        existing_prompts = db.query(PromptTemplate).count()
        if existing_prompts > 0:
            return

        # Prompt de clasificación por defecto
        classification_prompt = PromptTemplate(
            name="default_classification",
            prompt_type="classification",
            document_type=None,
            prompt_template="""Analiza el siguiente contenido de documento y clasifícalo en una de estas categorías:
- factura
- orden_compra
- certificado_origen
- especificacion_tecnica
- contrato
- remito
- otro

Contenido del documento:
{text_content}

Responde ÚNICAMENTE con un JSON en el siguiente formato:
{{"document_type": "tipo_de_documento", "confidence": 0.95, "reasoning": "breve explicación"}}""",
            description="Prompt por defecto para clasificación de documentos",
            is_active=1,
            variables={
                "text_content": "Contenido de texto del documento (primeros 3000 caracteres)"
            }
        )

        # Prompts de extracción por tipo de documento
        extraction_prompts = [
            {
                "name": "extraction_factura",
                "document_type": "factura",
                "fields": ["numero_factura", "fecha", "proveedor", "cliente", "monto_total", "moneda", "items"]
            },
            {
                "name": "extraction_orden_compra",
                "document_type": "orden_compra",
                "fields": ["numero_orden", "fecha", "proveedor", "cliente", "items", "monto_total"]
            },
            {
                "name": "extraction_certificado_origen",
                "document_type": "certificado_origen",
                "fields": ["numero_certificado", "fecha", "pais_origen", "producto", "exportador"]
            },
            {
                "name": "extraction_especificacion_tecnica",
                "document_type": "especificacion_tecnica",
                "fields": ["producto", "modelo", "especificaciones", "normas"]
            },
            {
                "name": "extraction_contrato",
                "document_type": "contrato",
                "fields": ["numero_contrato", "fecha", "partes", "objeto", "monto"]
            },
            {
                "name": "extraction_remito",
                "document_type": "remito",
                "fields": ["numero_remito", "fecha", "origen", "destino", "items"]
            }
        ]

        prompts_to_add = [classification_prompt]

        for extraction_config in extraction_prompts:
            prompt = PromptTemplate(
                name=extraction_config["name"],
                prompt_type="extraction",
                document_type=extraction_config["document_type"],
                prompt_template=f"""Extrae la siguiente información del documento de tipo "{extraction_config["document_type"]}":

Campos a extraer: {', '.join(extraction_config["fields"])}

Contenido del documento:
{{text_content}}

Responde ÚNICAMENTE con un JSON con los campos encontrados. Si un campo no está presente, usa null.
Formato de respuesta:
{{
  "campo1": "valor1",
  "campo2": "valor2",
  ...
}}""",
                description=f"Prompt por defecto para extracción de datos de {extraction_config['document_type']}",
                is_active=1,
                variables={
                    "text_content": "Contenido de texto del documento (primeros 4000 caracteres)",
                    "document_type": extraction_config["document_type"]
                }
            )
            prompts_to_add.append(prompt)

        # Agregar todos los prompts a la BD
        db.add_all(prompts_to_add)
        db.commit()


prompt_service = PromptService()
