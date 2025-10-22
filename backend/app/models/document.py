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
    document_type = Column(String(100))  # factura, orden_compra, certificado, etc.
    classification_confidence = Column(Float)
    extracted_data = Column(JSON)  # Datos extraídos del documento
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
    extracted_data = Column(JSON)  # Datos extraídos del documento
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
