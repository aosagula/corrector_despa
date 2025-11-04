from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import traceback

from ...core.database import get_db
from ...models.document import PageType, PageTypeDetectionRule, AttributeExtractionCoordinate
from ...schemas.page_type import (
    PageTypeCreate,
    PageTypeUpdate,
    PageTypeResponse,
    PageTypeListResponse,
    PageTypeWithRulesResponse,
    DetectionRuleCreate,
    DetectionRuleUpdate,
    DetectionRuleResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


# Page Types CRUD
@router.post("/", response_model=PageTypeResponse)
async def create_page_type(
    page_type: PageTypeCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo tipo de página"""
    try:
        # Verificar si ya existe
        existing = db.query(PageType).filter(PageType.name == page_type.name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"El tipo de página '{page_type.name}' ya existe")

        db_page_type = PageType(**page_type.dict())
        db.add(db_page_type)
        db.commit()
        db.refresh(db_page_type)

        return db_page_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating page type: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=List[PageTypeListResponse])
async def list_page_types(
    db: Session = Depends(get_db)
):
    """Lista todos los tipos de páginas con conteo de reglas"""
    try:
        page_types = db.query(PageType).all()

        # Agregar el conteo de reglas a cada tipo de página
        result = []
        for pt in page_types:
            pt_dict = {
                "id": pt.id,
                "name": pt.name,
                "display_name": pt.display_name,
                "description": pt.description,
                "color": pt.color,
                "created_at": pt.created_at,
                "updated_at": pt.updated_at,
                "rules_count": len(pt.detection_rules)
            }
            result.append(pt_dict)

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing page types: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{page_type_id}", response_model=PageTypeWithRulesResponse)
async def get_page_type(
    page_type_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un tipo de página con sus reglas de detección"""
    try:
        page_type = db.query(PageType).filter(PageType.id == page_type_id).first()

        if not page_type:
            raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

        return page_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page type {page_type_id}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{page_type_id}", response_model=PageTypeResponse)
async def update_page_type(
    page_type_id: int,
    page_type_update: PageTypeUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza un tipo de página"""
    try:
        db_page_type = db.query(PageType).filter(PageType.id == page_type_id).first()

        if not db_page_type:
            raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

        update_data = page_type_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_page_type, key, value)

        db.commit()
        db.refresh(db_page_type)

        return db_page_type
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating page type {page_type_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/{page_type_id}")
async def delete_page_type(
    page_type_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un tipo de página"""
    try:
        db_page_type = db.query(PageType).filter(PageType.id == page_type_id).first()

        if not db_page_type:
            raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

        db.delete(db_page_type)
        db.commit()

        return {"message": "Tipo de página eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting page type {page_type_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# Detection Rules CRUD
@router.post("/{page_type_id}/rules", response_model=DetectionRuleResponse)
async def create_detection_rule(
    page_type_id: int,
    rule: DetectionRuleCreate,
    db: Session = Depends(get_db)
):
    """Crea una nueva regla de detección para un tipo de página"""
    try:
        # Verificar que el tipo de página existe
        page_type = db.query(PageType).filter(PageType.id == page_type_id).first()
        if not page_type:
            raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

        # Verificar que el page_type_id coincide
        if rule.page_type_id != page_type_id:
            raise HTTPException(status_code=400, detail="El page_type_id no coincide con la ruta")

        db_rule = PageTypeDetectionRule(**rule.dict())
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)

        return db_rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating detection rule for page type {page_type_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{page_type_id}/rules", response_model=List[DetectionRuleResponse])
async def list_detection_rules(
    page_type_id: int,
    db: Session = Depends(get_db)
):
    """Lista todas las reglas de detección de un tipo de página"""
    try:
        rules = db.query(PageTypeDetectionRule).filter(
            PageTypeDetectionRule.page_type_id == page_type_id
        ).order_by(PageTypeDetectionRule.priority.desc()).all()

        return rules
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing detection rules for page type {page_type_id}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/rules/{rule_id}", response_model=DetectionRuleResponse)
async def update_detection_rule(
    rule_id: int,
    rule_update: DetectionRuleUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza una regla de detección"""
    try:
        db_rule = db.query(PageTypeDetectionRule).filter(
            PageTypeDetectionRule.id == rule_id
        ).first()

        if not db_rule:
            raise HTTPException(status_code=404, detail="Regla de detección no encontrada")

        update_data = rule_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_rule, key, value)

        db.commit()
        db.refresh(db_rule)

        return db_rule
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating detection rule {rule_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/rules/{rule_id}")
async def delete_detection_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Elimina una regla de detección"""
    try:
        db_rule = db.query(PageTypeDetectionRule).filter(
            PageTypeDetectionRule.id == rule_id
        ).first()

        if not db_rule:
            raise HTTPException(status_code=404, detail="Regla de detección no encontrada")

        db.delete(db_rule)
        db.commit()

        return {"message": "Regla de detección eliminada exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting detection rule {rule_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# Extraction Coordinates for Page Types
@router.get("/{page_type_id}/extraction-coordinates")
async def list_extraction_coordinates(
    page_type_id: int,
    db: Session = Depends(get_db)
):
    """Lista todas las coordenadas de extracción de atributos para un tipo de página"""
    try:
        # Verificar que el tipo de página existe
        page_type = db.query(PageType).filter(PageType.id == page_type_id).first()
        if not page_type:
            raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

        coordinates = db.query(AttributeExtractionCoordinate).filter(
            AttributeExtractionCoordinate.page_type_id == page_type_id
        ).all()

        return coordinates
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing extraction coordinates for page type {page_type_id}: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
