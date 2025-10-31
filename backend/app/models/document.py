from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey, LargeBinary
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
    images = relationship("ProvisionalDocumentImage", back_populates="document", cascade="all, delete-orphan")


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


class ProvisionalDocumentImage(Base):
    """Modelo para imágenes de documentos provisorios (una imagen por página)"""
    __tablename__ = "provisional_document_images"

    id = Column(Integer, primary_key=True, index=True)
    provisional_document_id = Column(Integer, ForeignKey("provisional_documents.id"), nullable=False)
    page_number = Column(Integer, nullable=False)  # Número de página (1-based)
    image_data = Column(LargeBinary, nullable=False)  # Imagen en formato PNG B&N 300 DPI
    width = Column(Integer)  # Ancho de la imagen en píxeles
    height = Column(Integer)  # Alto de la imagen en píxeles
    page_type_id = Column(Integer, ForeignKey("page_types.id"))  # Tipo de página detectado
    detection_confidence = Column(Float)  # Confianza en la detección (0-1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    document = relationship("ProvisionalDocument", back_populates="images")
    page_type = relationship("PageType")


class PageType(Base):
    """Modelo para tipos de páginas (caratula, items, percepcion, anexos, datos_adicionales)"""
    __tablename__ = "page_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)  # caratula, items, percepcion, etc.
    display_name = Column(String(200), nullable=False)  # Nombre para mostrar
    description = Column(Text)  # Descripción del tipo de página
    color = Column(String(20), default="#007bff")  # Color para visualización en UI
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    detection_rules = relationship("PageTypeDetectionRule", back_populates="page_type", cascade="all, delete-orphan")
    coordinates = relationship("AttributeExtractionCoordinate", back_populates="page_type", cascade="all, delete-orphan")


class PageTypeDetectionRule(Base):
    """Modelo para reglas de detección automática de tipos de páginas"""
    __tablename__ = "page_type_detection_rules"

    id = Column(Integer, primary_key=True, index=True)
    page_type_id = Column(Integer, ForeignKey("page_types.id"), nullable=False)
    attribute_name = Column(String(100), nullable=False)  # Nombre del atributo a buscar
    x1 = Column(Integer, nullable=False)  # Coordenada del box de detección
    y1 = Column(Integer, nullable=False)
    x2 = Column(Integer, nullable=False)
    y2 = Column(Integer, nullable=False)
    expected_value = Column(String(500))  # Valor esperado (puede ser regex, texto, número, fecha)
    match_type = Column(String(20), default="contains")  # contains, not_contains, exact, not_exact, regex (para text)
    data_type = Column(String(20), default="text")  # text, number, date
    comparator = Column(String(20), default="contains")  # Para text: contains, not_contains, exact, not_exact, regex. Para number/date: eq, ne, gt, lt, gte, lte
    date_format = Column(String(50))  # Formato de fecha para parsing (ej: %d/%m/%Y)
    priority = Column(Integer, default=0)  # Prioridad de la regla (mayor = más importante)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    page_type = relationship("PageType", back_populates="detection_rules")


class AttributeExtractionCoordinate(Base):
    """Modelo para coordenadas de extracción de atributos"""
    __tablename__ = "attribute_extraction_coordinates"

    id = Column(Integer, primary_key=True, index=True)
    page_type_id = Column(Integer, ForeignKey("page_types.id"), nullable=False)  # Asociado a tipo de página
    attribute_id = Column(Integer, ForeignKey("configurable_attributes.id"), nullable=False)
    x1 = Column(Integer, nullable=False)  # Coordenada superior izquierda X
    y1 = Column(Integer, nullable=False)  # Coordenada superior izquierda Y
    x2 = Column(Integer, nullable=False)  # Coordenada inferior derecha X
    y2 = Column(Integer, nullable=False)  # Coordenada inferior derecha Y
    label = Column(String(100), nullable=False)  # Nombre del atributo para esta coordenada
    description = Column(Text)  # Descripción de qué se extrae en esta área
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relaciones
    page_type = relationship("PageType", back_populates="coordinates")


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
