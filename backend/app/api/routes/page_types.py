from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.document import PageType, PageTypeDetectionRule
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

router = APIRouter()


# Page Types CRUD
@router.post("/", response_model=PageTypeResponse)
async def create_page_type(
    page_type: PageTypeCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo tipo de página"""
    # Verificar si ya existe
    existing = db.query(PageType).filter(PageType.name == page_type.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"El tipo de página '{page_type.name}' ya existe")

    db_page_type = PageType(**page_type.dict())
    db.add(db_page_type)
    db.commit()
    db.refresh(db_page_type)

    return db_page_type


@router.get("/", response_model=List[PageTypeListResponse])
async def list_page_types(
    db: Session = Depends(get_db)
):
    """Lista todos los tipos de páginas con conteo de reglas"""
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


@router.get("/{page_type_id}", response_model=PageTypeWithRulesResponse)
async def get_page_type(
    page_type_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un tipo de página con sus reglas de detección"""
    page_type = db.query(PageType).filter(PageType.id == page_type_id).first()

    if not page_type:
        raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

    return page_type


@router.put("/{page_type_id}", response_model=PageTypeResponse)
async def update_page_type(
    page_type_id: int,
    page_type_update: PageTypeUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza un tipo de página"""
    db_page_type = db.query(PageType).filter(PageType.id == page_type_id).first()

    if not db_page_type:
        raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

    update_data = page_type_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_page_type, key, value)

    db.commit()
    db.refresh(db_page_type)

    return db_page_type


@router.delete("/{page_type_id}")
async def delete_page_type(
    page_type_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un tipo de página"""
    db_page_type = db.query(PageType).filter(PageType.id == page_type_id).first()

    if not db_page_type:
        raise HTTPException(status_code=404, detail="Tipo de página no encontrado")

    db.delete(db_page_type)
    db.commit()

    return {"message": "Tipo de página eliminado exitosamente"}


# Detection Rules CRUD
@router.post("/{page_type_id}/rules", response_model=DetectionRuleResponse)
async def create_detection_rule(
    page_type_id: int,
    rule: DetectionRuleCreate,
    db: Session = Depends(get_db)
):
    """Crea una nueva regla de detección para un tipo de página"""
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


@router.get("/{page_type_id}/rules", response_model=List[DetectionRuleResponse])
async def list_detection_rules(
    page_type_id: int,
    db: Session = Depends(get_db)
):
    """Lista todas las reglas de detección de un tipo de página"""
    rules = db.query(PageTypeDetectionRule).filter(
        PageTypeDetectionRule.page_type_id == page_type_id
    ).order_by(PageTypeDetectionRule.priority.desc()).all()

    return rules


@router.put("/rules/{rule_id}", response_model=DetectionRuleResponse)
async def update_detection_rule(
    rule_id: int,
    rule_update: DetectionRuleUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza una regla de detección"""
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


@router.delete("/rules/{rule_id}")
async def delete_detection_rule(
    rule_id: int,
    db: Session = Depends(get_db)
):
    """Elimina una regla de detección"""
    db_rule = db.query(PageTypeDetectionRule).filter(
        PageTypeDetectionRule.id == rule_id
    ).first()

    if not db_rule:
        raise HTTPException(status_code=404, detail="Regla de detección no encontrada")

    db.delete(db_rule)
    db.commit()

    return {"message": "Regla de detección eliminada exitosamente"}
