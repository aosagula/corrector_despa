from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...models.document import Comparison, CommercialDocument, ProvisionalDocument
from ...schemas.document import ComparisonCreate, ComparisonResponse
from ...services.comparison_service import comparison_service

router = APIRouter()


@router.post("/", response_model=ComparisonResponse)
async def create_comparison(
    comparison: ComparisonCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva comparación entre un documento comercial y uno provisorio

    - Obtiene los datos de ambos documentos
    - Compara los atributos configurables
    - Guarda el resultado en la base de datos
    """
    # Verificar que existan ambos documentos
    commercial_doc = db.query(CommercialDocument).filter(
        CommercialDocument.id == comparison.commercial_document_id
    ).first()

    if not commercial_doc:
        raise HTTPException(status_code=404, detail="Documento comercial no encontrado")

    provisional_doc = db.query(ProvisionalDocument).filter(
        ProvisionalDocument.id == comparison.provisional_document_id
    ).first()

    if not provisional_doc:
        raise HTTPException(status_code=404, detail="Documento provisorio no encontrado")

    # Realizar la comparación
    comparison_result = comparison_service.compare_documents(
        commercial_data=commercial_doc.extracted_data or {},
        provisional_data=provisional_doc.extracted_data or {},
        db=db
    )

    # Guardar resultado en base de datos
    db_comparison = Comparison(
        commercial_document_id=comparison.commercial_document_id,
        provisional_document_id=comparison.provisional_document_id,
        comparison_result=comparison_result,
        match_percentage=comparison_result["match_percentage"],
        status=comparison_result["status"]
    )

    db.add(db_comparison)
    db.commit()
    db.refresh(db_comparison)

    return db_comparison


@router.get("/", response_model=List[ComparisonResponse])
async def list_comparisons(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Lista todas las comparaciones realizadas"""
    query = db.query(Comparison)

    if status:
        query = query.filter(Comparison.status == status)

    comparisons = query.offset(skip).limit(limit).all()
    return comparisons


@router.get("/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una comparación específica"""
    comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()

    if not comparison:
        raise HTTPException(status_code=404, detail="Comparación no encontrada")

    return comparison


@router.post("/batch")
async def batch_comparison(
    provisional_document_id: int,
    db: Session = Depends(get_db)
):
    """
    Compara un documento provisorio con todos los documentos comerciales

    Retorna todas las comparaciones realizadas
    """
    # Verificar que exista el documento provisorio
    provisional_doc = db.query(ProvisionalDocument).filter(
        ProvisionalDocument.id == provisional_document_id
    ).first()

    if not provisional_doc:
        raise HTTPException(status_code=404, detail="Documento provisorio no encontrado")

    # Obtener todos los documentos comerciales
    commercial_docs = db.query(CommercialDocument).all()

    if not commercial_docs:
        raise HTTPException(status_code=404, detail="No hay documentos comerciales para comparar")

    results = []

    for commercial_doc in commercial_docs:
        # Realizar comparación
        comparison_result = comparison_service.compare_documents(
            commercial_data=commercial_doc.extracted_data or {},
            provisional_data=provisional_doc.extracted_data or {},
            db=db
        )

        # Guardar resultado
        db_comparison = Comparison(
            commercial_document_id=commercial_doc.id,
            provisional_document_id=provisional_document_id,
            comparison_result=comparison_result,
            match_percentage=comparison_result["match_percentage"],
            status=comparison_result["status"]
        )

        db.add(db_comparison)
        results.append({
            "comparison_id": None,  # Se asignará después del commit
            "commercial_document_id": commercial_doc.id,
            "commercial_document_type": commercial_doc.document_type,
            "match_percentage": comparison_result["match_percentage"],
            "status": comparison_result["status"],
            "comparison_details": comparison_result["comparisons"]
        })

    db.commit()

    return {
        "message": f"Se realizaron {len(results)} comparaciones",
        "results": results
    }
