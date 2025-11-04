from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import traceback

from ...core.database import get_db
from ...models.document import ConfigurableAttribute
from ...schemas.document import (
    ConfigurableAttributeCreate,
    ConfigurableAttributeUpdate,
    ConfigurableAttributeResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=ConfigurableAttributeResponse)
async def create_attribute(
    attribute: ConfigurableAttributeCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo atributo configurable"""
    try:
        logger.info(f"Intentando crear atributo: {attribute.attribute_name}")
        logger.debug(f"Datos del atributo: {attribute.model_dump()}")

        # Verificar que no exista ya un atributo con el mismo nombre
        existing = db.query(ConfigurableAttribute).filter(
            ConfigurableAttribute.attribute_name == attribute.attribute_name
        ).first()

        if existing:
            logger.warning(f"Atributo duplicado detectado: {attribute.attribute_name} (ID existente: {existing.id})")
            raise HTTPException(
                status_code=400,
                detail="Ya existe un atributo con ese nombre"
            )

        db_attribute = ConfigurableAttribute(**attribute.model_dump())
        db.add(db_attribute)
        db.commit()
        db.refresh(db_attribute)

        return db_attribute
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creando atributo: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=List[ConfigurableAttributeResponse])
async def list_attributes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista todos los atributos configurables"""
    try:
        attributes = db.query(ConfigurableAttribute).offset(skip).limit(limit).all()
        return attributes
    except Exception as e:
        logger.error(f"Error listando atributos: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{attribute_id}", response_model=ConfigurableAttributeResponse)
async def get_attribute(
    attribute_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un atributo específico"""
    try:
        attribute = db.query(ConfigurableAttribute).filter(
            ConfigurableAttribute.id == attribute_id
        ).first()

        if not attribute:
            raise HTTPException(status_code=404, detail="Atributo no encontrado")

        return attribute
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo atributo {attribute_id}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{attribute_id}", response_model=ConfigurableAttributeResponse)
async def update_attribute(
    attribute_id: int,
    attribute: ConfigurableAttributeUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza un atributo configurable"""
    try:
        db_attribute = db.query(ConfigurableAttribute).filter(
            ConfigurableAttribute.id == attribute_id
        ).first()

        if not db_attribute:
            raise HTTPException(status_code=404, detail="Atributo no encontrado")

        # Actualizar campos no nulos
        update_data = attribute.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_attribute, field, value)

        db.commit()
        db.refresh(db_attribute)

        return db_attribute
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando atributo {attribute_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/{attribute_id}")
async def delete_attribute(
    attribute_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un atributo configurable"""
    try:
        attribute = db.query(ConfigurableAttribute).filter(
            ConfigurableAttribute.id == attribute_id
        ).first()

        if not attribute:
            raise HTTPException(status_code=404, detail="Atributo no encontrado")

        db.delete(attribute)
        db.commit()

        return {"message": "Atributo eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando atributo {attribute_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/defaults")
async def create_default_attributes(db: Session = Depends(get_db)):
    """Crea atributos por defecto para empezar a usar el sistema"""
    try:
        default_attributes = [
            {
                "attribute_name": "Número de Documento",
                "attribute_key": "numero_factura",
                "description": "Número de factura o documento",
                "is_required": 1,
                "validation_rules": {"type": "text"}
            },
            {
                "attribute_name": "Fecha",
                "attribute_key": "fecha",
                "description": "Fecha del documento",
                "is_required": 1,
                "validation_rules": {"type": "date"}
            },
            {
                "attribute_name": "Proveedor",
                "attribute_key": "proveedor",
                "description": "Nombre del proveedor o emisor",
                "is_required": 1,
                "validation_rules": {"type": "text"}
            },
            {
                "attribute_name": "Monto Total",
                "attribute_key": "monto_total",
                "description": "Monto total del documento",
                "is_required": 1,
                "validation_rules": {"type": "numeric", "tolerance": 0.01}
            },
            {
                "attribute_name": "Moneda",
                "attribute_key": "moneda",
                "description": "Tipo de moneda",
                "is_required": 0,
                "validation_rules": {"type": "text"}
            },
            {
                "attribute_name": "Cliente",
                "attribute_key": "cliente",
                "description": "Nombre del cliente o receptor",
                "is_required": 0,
                "validation_rules": {"type": "text"}
            }
        ]

        created = []
        for attr_data in default_attributes:
            # Verificar si ya existe
            existing = db.query(ConfigurableAttribute).filter(
                ConfigurableAttribute.attribute_name == attr_data["attribute_name"]
            ).first()

            if not existing:
                db_attribute = ConfigurableAttribute(**attr_data)
                db.add(db_attribute)
                created.append(attr_data["attribute_name"])

        db.commit()

        return {
            "message": "Atributos por defecto creados",
            "created": created
        }
    except Exception as e:
        logger.error(f"Error creando atributos por defecto: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
