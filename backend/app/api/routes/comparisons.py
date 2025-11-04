from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import traceback

from ...core.database import get_db
from ...models.document import Comparison, CommercialDocument, ProvisionalDocument
from ...schemas.document import ComparisonCreate, ComparisonResponse
from ...services.comparison_service import comparison_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=ComparisonResponse)
async def create_comparison(
    comparison: ComparisonCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva comparación entre un documento comercial y uno provisorio

    - Obtiene los datos de ambos documentos
    - Valida que compartan la misma referencia (si está configurada)
    - Compara los atributos configurables
    - Guarda el resultado en la base de datos
    """
    try:
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

        # Validar que compartan la misma referencia (si al menos uno tiene referencia)
        if commercial_doc.reference or provisional_doc.reference:
            if commercial_doc.reference != provisional_doc.reference:
                raise HTTPException(
                    status_code=400,
                    detail=f"Los documentos deben compartir la misma referencia. "
                           f"Comercial: '{commercial_doc.reference or 'sin referencia'}', "
                           f"Provisorio: '{provisional_doc.reference or 'sin referencia'}'"
                )

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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comparison: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=List[ComparisonResponse])
async def list_comparisons(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Lista todas las comparaciones realizadas"""
    try:
        query = db.query(Comparison)

        if status:
            query = query.filter(Comparison.status == status)

        comparisons = query.offset(skip).limit(limit).all()
        return comparisons
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing comparisons: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{comparison_id}", response_model=ComparisonResponse)
async def get_comparison(
    comparison_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una comparación específica"""
    try:
        comparison = db.query(Comparison).filter(Comparison.id == comparison_id).first()

        if not comparison:
            raise HTTPException(status_code=404, detail="Comparación no encontrada")

        return comparison
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comparison: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/batch")
async def batch_comparison(
    provisional_document_id: int,
    db: Session = Depends(get_db)
):
    """
    Compara un documento provisorio con documentos comerciales que compartan la misma referencia

    Si el documento provisorio tiene referencia, solo compara con comerciales de la misma referencia.
    Si no tiene referencia, compara con todos los comerciales sin referencia.

    Retorna todas las comparaciones realizadas
    """
    try:
        # Verificar que exista el documento provisorio
        provisional_doc = db.query(ProvisionalDocument).filter(
            ProvisionalDocument.id == provisional_document_id
        ).first()

        if not provisional_doc:
            raise HTTPException(status_code=404, detail="Documento provisorio no encontrado")

        # Obtener documentos comerciales filtrados por referencia
        query = db.query(CommercialDocument)

        if provisional_doc.reference:
            # Solo documentos con la misma referencia
            query = query.filter(CommercialDocument.reference == provisional_doc.reference)
        else:
            # Solo documentos sin referencia
            query = query.filter(CommercialDocument.reference.is_(None))

        commercial_docs = query.all()

        if not commercial_docs:
            reference_msg = f"con la referencia '{provisional_doc.reference}'" if provisional_doc.reference else "sin referencia"
            raise HTTPException(
                status_code=404,
                detail=f"No hay documentos comerciales {reference_msg} para comparar"
            )

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
                "commercial_reference": commercial_doc.reference,
                "match_percentage": comparison_result["match_percentage"],
                "status": comparison_result["status"],
                "comparison_details": comparison_result["comparisons"]
            })

        db.commit()

        reference_info = f" con referencia '{provisional_doc.reference}'" if provisional_doc.reference else " sin referencia"
        return {
            "message": f"Se realizaron {len(results)} comparaciones{reference_info}",
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch comparison: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
