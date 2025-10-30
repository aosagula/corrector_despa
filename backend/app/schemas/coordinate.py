from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CoordinateBase(BaseModel):
    """Schema base para coordenadas de extracción"""
    attribute_id: int = Field(..., description="ID del atributo asociado")
    page_number: int = Field(..., ge=1, description="Número de página (1-based)")
    x1: int = Field(..., ge=0, description="Coordenada X superior izquierda")
    y1: int = Field(..., ge=0, description="Coordenada Y superior izquierda")
    x2: int = Field(..., gt=0, description="Coordenada X inferior derecha")
    y2: int = Field(..., gt=0, description="Coordenada Y inferior derecha")
    label: str = Field(..., max_length=100, description="Etiqueta del atributo")
    description: Optional[str] = Field(None, description="Descripción del área de extracción")


class CoordinateCreate(CoordinateBase):
    """Schema para crear una coordenada"""
    pass


class CoordinateUpdate(BaseModel):
    """Schema para actualizar una coordenada"""
    page_number: Optional[int] = Field(None, ge=1)
    x1: Optional[int] = Field(None, ge=0)
    y1: Optional[int] = Field(None, ge=0)
    x2: Optional[int] = Field(None, gt=0)
    y2: Optional[int] = Field(None, gt=0)
    label: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class CoordinateResponse(CoordinateBase):
    """Schema de respuesta para coordenadas"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
