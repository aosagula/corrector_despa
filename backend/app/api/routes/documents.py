from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path

from ...core.database import get_db
from ...core.config import settings
from ...models.document import CommercialDocument, ProvisionalDocument
from ...schemas.document import (
    CommercialDocumentResponse,
    ProvisionalDocumentResponse,
    UploadResponse
)
from ...services.ocr_service import ocr_service
from ...services.llama_service import llama_service

router = APIRouter()

# Crear directorio de uploads si no existe
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/commercial", response_model=UploadResponse)
async def upload_commercial_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Sube y procesa un documento comercial

    - Extrae el texto del documento
    - Clasifica el tipo de documento usando Phi-4
    - Extrae datos estructurados
    - Guarda en la base de datos
    """
    # Validar extensión de archivo
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Guardar archivo
    file_path = UPLOAD_DIR / f"commercial_{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")

    try:
        # Extraer texto
        text_content = ocr_service.extract_text(str(file_path), file_extension)

        if not text_content:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del documento")

        # Clasificar documento
        classification_result = llama_service.classify_document(text_content, db)
        document_type = classification_result.get("document_type", "desconocido")
        confidence = classification_result.get("confidence", 0.0)

        # Extraer datos estructurados
        extracted_data = llama_service.extract_structured_data(text_content, document_type, db)
        extracted_data["classification_reasoning"] = classification_result.get("reasoning", "")

        # Guardar en base de datos
        db_document = CommercialDocument(
            filename=file.filename,
            file_path=str(file_path),
            document_type=document_type,
            classification_confidence=confidence,
            extracted_data=extracted_data
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        return UploadResponse(
            message="Documento comercial subido y procesado exitosamente",
            document_id=db_document.id,
            filename=file.filename,
            document_type=document_type,
            extracted_data=extracted_data,
            classification_confidence=confidence
        )

    except Exception as e:
        db.rollback()
        # Eliminar archivo si hubo error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")


@router.post("/provisional", response_model=UploadResponse)
async def upload_provisional_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Sube y procesa un documento provisorio para validación

    - Extrae el texto del documento
    - Extrae datos estructurados
    - Guarda en la base de datos
    """
    # Validar extensión de archivo
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión no permitida. Use: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Guardar archivo
    file_path = UPLOAD_DIR / f"provisional_{file.filename}"
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")

    try:
        # Extraer texto
        text_content = ocr_service.extract_text(str(file_path), file_extension)

        if not text_content:
            raise HTTPException(status_code=400, detail="No se pudo extraer texto del documento")

        # Extraer datos estructurados (asumiendo que es una factura genérica)
        extracted_data = llama_service.extract_structured_data(text_content, "factura", db)

        # Guardar en base de datos
        db_document = ProvisionalDocument(
            filename=file.filename,
            file_path=str(file_path),
            extracted_data=extracted_data
        )

        db.add(db_document)
        db.commit()
        db.refresh(db_document)

        return UploadResponse(
            message="Documento provisorio subido y procesado exitosamente",
            document_id=db_document.id,
            filename=file.filename,
            extracted_data=extracted_data
        )

    except Exception as e:
        db.rollback()
        # Eliminar archivo si hubo error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")


@router.get("/commercial", response_model=List[CommercialDocumentResponse])
async def list_commercial_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista todos los documentos comerciales"""
    query = db.query(CommercialDocument)

    if document_type:
        query = query.filter(CommercialDocument.document_type == document_type)

    documents = query.offset(skip).limit(limit).all()
    return documents


@router.get("/commercial/{document_id}", response_model=CommercialDocumentResponse)
async def get_commercial_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un documento comercial específico"""
    document = db.query(CommercialDocument).filter(CommercialDocument.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return document


@router.get("/provisional", response_model=List[ProvisionalDocumentResponse])
async def list_provisional_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista todos los documentos provisorios"""
    documents = db.query(ProvisionalDocument).offset(skip).limit(limit).all()
    return documents


@router.get("/provisional/{document_id}", response_model=ProvisionalDocumentResponse)
async def get_provisional_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un documento provisorio específico"""
    document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    return document


@router.delete("/commercial/{document_id}")
async def delete_commercial_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un documento comercial"""
    document = db.query(CommercialDocument).filter(CommercialDocument.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Eliminar archivo físico
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {"message": "Documento eliminado exitosamente"}


@router.delete("/provisional/{document_id}")
async def delete_provisional_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un documento provisorio"""
    document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Eliminar archivo físico
    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    db.delete(document)
    db.commit()

    return {"message": "Documento eliminado exitosamente"}
