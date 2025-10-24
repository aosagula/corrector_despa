from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class CommercialDocumentBase(BaseModel):
    filename: str
    reference: Optional[str] = None
    document_type: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None


class CommercialDocumentCreate(CommercialDocumentBase):
    file_path: str


class CommercialDocumentResponse(CommercialDocumentBase):
    id: int
    file_path: str
    classification_confidence: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProvisionalDocumentBase(BaseModel):
    filename: str
    reference: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None


class ProvisionalDocumentCreate(ProvisionalDocumentBase):
    file_path: str


class ProvisionalDocumentResponse(ProvisionalDocumentBase):
    id: int
    file_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConfigurableAttributeBase(BaseModel):
    attribute_name: str
    attribute_key: str
    description: Optional[str] = None
    is_required: int = 0
    validation_rules: Optional[Dict[str, Any]] = None


class ConfigurableAttributeCreate(ConfigurableAttributeBase):
    pass


class ConfigurableAttributeUpdate(BaseModel):
    attribute_name: Optional[str] = None
    attribute_key: Optional[str] = None
    description: Optional[str] = None
    is_required: Optional[int] = None
    validation_rules: Optional[Dict[str, Any]] = None


class ConfigurableAttributeResponse(ConfigurableAttributeBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComparisonBase(BaseModel):
    commercial_document_id: int
    provisional_document_id: int


class ComparisonCreate(ComparisonBase):
    pass


class ComparisonResponse(ComparisonBase):
    id: int
    comparison_result: Dict[str, Any]
    match_percentage: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ComparisonDetail(BaseModel):
    """Detalle de una comparación individual de atributos"""
    attribute_name: str
    commercial_value: Any
    provisional_value: Any
    match: bool
    confidence: Optional[float] = None


class UploadResponse(BaseModel):
    message: str
    document_id: int
    filename: str
    document_type: Optional[str] = None
    extracted_data: Dict[str, Any]
    classification_confidence: Optional[float] = None


class PromptTemplateBase(BaseModel):
    name: str
    prompt_type: str = Field(..., description="classification o extraction")
    document_type: Optional[str] = Field(None, description="Tipo de documento para extraction, null para classification")
    prompt_template: str = Field(..., description="Template del prompt con variables como {{text_content}}, {{document_type}}")
    description: Optional[str] = None
    is_active: int = Field(1, description="1=activo, 0=inactivo")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variables disponibles en el template")
    response_format: str = Field('text', description="Formato de respuesta: 'text' o 'json'")
    json_schema: Optional[Dict[str, Any]] = Field(None, description="Esquema JSON de ejemplo si response_format='json'")


class PromptTemplateCreate(PromptTemplateBase):
    pass


class PromptTemplateUpdate(BaseModel):
    name: Optional[str] = None
    prompt_type: Optional[str] = None
    document_type: Optional[str] = None
    prompt_template: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[int] = None
    variables: Optional[Dict[str, Any]] = None
    response_format: Optional[str] = None
    json_schema: Optional[Dict[str, Any]] = None


class PromptTemplateResponse(PromptTemplateBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
