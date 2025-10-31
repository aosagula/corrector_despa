from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# PageType Schemas
class PageTypeBase(BaseModel):
    """Schema base para tipos de páginas"""
    name: str = Field(..., max_length=100, description="Identificador único del tipo")
    display_name: str = Field(..., max_length=200, description="Nombre para mostrar")
    description: Optional[str] = Field(None, description="Descripción del tipo de página")
    color: str = Field(default="#007bff", max_length=20, description="Color hex para UI")


class PageTypeCreate(PageTypeBase):
    """Schema para crear un tipo de página"""
    pass


class PageTypeUpdate(BaseModel):
    """Schema para actualizar un tipo de página"""
    display_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=20)


class PageTypeResponse(PageTypeBase):
    """Schema de respuesta para tipos de páginas"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PageTypeListResponse(PageTypeBase):
    """Schema de respuesta para listado de tipos de páginas (incluye conteo de reglas)"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    rules_count: int = Field(default=0, description="Número de reglas de detección")

    class Config:
        from_attributes = True


# Detection Rule Schemas
class DetectionRuleBase(BaseModel):
    """Schema base para reglas de detección"""
    page_type_id: int
    attribute_name: str = Field(..., max_length=100, description="Nombre del atributo a buscar")
    x1: int = Field(..., ge=0)
    y1: int = Field(..., ge=0)
    x2: int = Field(..., gt=0)
    y2: int = Field(..., gt=0)
    expected_value: Optional[str] = Field(None, max_length=500, description="Valor esperado")
    match_type: str = Field(default="contains", description="Tipo de coincidencia: contains, exact, regex")
    priority: int = Field(default=0, description="Prioridad de la regla")


class DetectionRuleCreate(DetectionRuleBase):
    """Schema para crear una regla de detección"""
    pass


class DetectionRuleUpdate(BaseModel):
    """Schema para actualizar una regla de detección"""
    attribute_name: Optional[str] = Field(None, max_length=100)
    x1: Optional[int] = Field(None, ge=0)
    y1: Optional[int] = Field(None, ge=0)
    x2: Optional[int] = Field(None, gt=0)
    y2: Optional[int] = Field(None, gt=0)
    expected_value: Optional[str] = Field(None, max_length=500)
    match_type: Optional[str] = None
    priority: Optional[int] = None


class DetectionRuleResponse(DetectionRuleBase):
    """Schema de respuesta para reglas de detección"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Complete PageType with rules
class PageTypeWithRulesResponse(PageTypeResponse):
    """Schema de respuesta completo con reglas de detección"""
    detection_rules: List[DetectionRuleResponse] = []

    class Config:
        from_attributes = True
