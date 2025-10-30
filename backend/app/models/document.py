from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base


class CommercialDocument(Base):
    """Modelo para documentos comerciales (facturas, órdenes de compra, etc.)"""
    __tablename__ = "commercial_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    reference = Column(String(100), index=True)  # Referencia para agrupar documentos relacionados
    document_type = Column(String(100))  # factura, orden_compra, certificado, etc.
    classification_confidence = Column(Float)
    extraction_model = Column(String(100))  # Modelo usado para extracción (phi4-mini, qwen2.5-vl:3b, etc.)
    extraction_prompt = Column(Text)  # Prompt usado para la extracción
    extracted_data = Column(JSON)  # Datos extraídos del documento
    text_content = Column(Text)  # Contenido de texto extraído del documento
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    comparisons = relationship("Comparison", back_populates="commercial_document")


class ProvisionalDocument(Base):
    """Modelo para documentos provisorios a validar"""
    __tablename__ = "provisional_documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    reference = Column(String(100), index=True)  # Referencia para agrupar documentos relacionados
    extraction_model = Column(String(100))  # Modelo usado para extracción (phi4-mini, qwen2.5-vl:3b, etc.)
    extraction_prompt = Column(Text)  # Prompt usado para la extracción
    extracted_data = Column(JSON)  # Datos extraídos del documento
    text_content = Column(Text)  # Contenido de texto extraído del documento
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    comparisons = relationship("Comparison", back_populates="provisional_document")


class ConfigurableAttribute(Base):
    """Modelo para atributos configurables a comparar"""
    __tablename__ = "configurable_attributes"

    id = Column(Integer, primary_key=True, index=True)
    attribute_name = Column(String(100), nullable=False, unique=True)
    attribute_key = Column(String(100), nullable=False)  # Key en el JSON de extracted_data
    description = Column(Text)
    is_required = Column(Integer, default=0)  # 0=opcional, 1=requerido
    validation_rules = Column(JSON)  # Reglas de validación personalizadas
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Comparison(Base):
    """Modelo para registrar comparaciones entre documentos"""
    __tablename__ = "comparisons"

    id = Column(Integer, primary_key=True, index=True)
    commercial_document_id = Column(Integer, ForeignKey("commercial_documents.id"))
    provisional_document_id = Column(Integer, ForeignKey("provisional_documents.id"))
    comparison_result = Column(JSON)  # Resultado detallado de la comparación
    match_percentage = Column(Float)
    status = Column(String(50))  # approved, rejected, pending_review
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    commercial_document = relationship("CommercialDocument", back_populates="comparisons")
    provisional_document = relationship("ProvisionalDocument", back_populates="comparisons")


class PromptTemplate(Base):
    """Modelo para plantillas de prompts configurables"""
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    prompt_type = Column(String(50), nullable=False)  # classification, extraction
    document_type = Column(String(100))  # null para classification, tipo específico para extraction
    prompt_template = Column(Text, nullable=False)
    description = Column(Text)
    is_active = Column(Integer, default=1)  # 0=inactivo, 1=activo
    variables = Column(JSON)  # Variables que el prompt puede usar: {{text_content}}, {{document_type}}, etc.
    response_format = Column(String(20), default='text')  # 'text' o 'json'
    json_schema = Column(JSON)  # Esquema JSON de ejemplo para la respuesta (si response_format='json')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
