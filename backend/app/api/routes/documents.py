from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from pathlib import Path
import logging
import traceback

logger = logging.getLogger(__name__)

from ...core.database import get_db
from ...core.config import settings
from ...models.document import CommercialDocument, ProvisionalDocument, ProvisionalDocumentImage
from ...schemas.document import (
    CommercialDocumentResponse,
    ProvisionalDocumentResponse,
    UploadResponse
)
from ...services.ocr_service import ocr_service
from ...services.llama_service import llama_service
from ...services.vision_service import vision_service
from ...services.pdf_to_image_service import pdf_to_image_service
from ...services.page_type_detection_service import PageTypeDetectionService

router = APIRouter()

# Crear directorio de uploads si no existe
UPLOAD_DIR = Path(settings.UPLOAD_DIR)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/commercial", response_model=UploadResponse)
async def upload_commercial_document(
    file: UploadFile = File(...),
    reference: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Sube y procesa un documento comercial

    - Extrae el texto del documento
    - Clasifica el tipo de documento usando Phi-4
    - Extrae datos estructurados
    - Guarda en la base de datos
    - Opcionalmente asocia una referencia para agrupar documentos
    """
    try:
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
            logger.error(f"Error guardando archivo comercial: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")

        try:
            # Extraer texto (siempre necesario para guardar en text_content)
            text_content = ocr_service.extract_text(str(file_path), file_extension)

            if not text_content:
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del documento")

            # Clasificar documento (siempre usa OCR/texto)
            classification_result = llama_service.classify_document(text_content, db)
            document_type = classification_result.get("document_type", "desconocido")
            confidence = classification_result.get("confidence", 0.0)

            # Extraer datos estructurados según método configurado
            if settings.EXTRACTION_METHOD == "vision":
                logger.info(f"Usando extracción basada en visión para {document_type}")
                extraction_model_used = settings.VISION_MODEL
                if file_extension == ".pdf":
                    extracted_data, extraction_prompt = vision_service.extract_from_pdf(str(file_path), document_type, db)
                else:
                    # Para imágenes directamente
                    extracted_data, extraction_prompt = vision_service.extract_from_image_file(str(file_path), document_type, db)
            else:
                logger.info(f"Usando extracción basada en OCR para {document_type}")
                extraction_model_used = settings.OLLAMA_MODEL
                extracted_data, extraction_prompt = llama_service.extract_structured_data(text_content, document_type, db)

            extracted_data["classification_reasoning"] = classification_result.get("reasoning", "")

            # Guardar en base de datos
            db_document = CommercialDocument(
                filename=file.filename,
                file_path=str(file_path),
                reference=reference,
                document_type=document_type,
                classification_confidence=confidence,
                extraction_model=extraction_model_used,
                extraction_prompt=extraction_prompt,
                extracted_data=extracted_data,
                text_content=text_content
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

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error procesando documento comercial: {str(e)}\n{traceback.format_exc()}")
            db.rollback()
            # Eliminar archivo si hubo error
            if file_path.exists():
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_commercial_document: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/provisional", response_model=UploadResponse)
async def upload_provisional_document(
    file: UploadFile = File(...),
    reference: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Sube y procesa un documento provisorio para validación

    - Extrae el texto del documento
    - Valida que sea un documento provisorio (debe contener: SUBREGIMEN, DECLARACION DE LA MERCADERIA, PROVISORIO)
    - Extrae datos estructurados
    - Guarda en la base de datos
    - Opcionalmente asocia una referencia para agrupar documentos
    """
    try:
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
            logger.error(f"Error guardando archivo provisional: {str(e)}\n{traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Error guardando archivo: {str(e)}")

        try:
            # Extraer texto (siempre necesario para guardar en text_content)
            text_content = ocr_service.extract_text(str(file_path), file_extension)

            if not text_content:
                raise HTTPException(status_code=400, detail="No se pudo extraer texto del documento")

            # Validar que sea un documento provisorio
            required_keywords = ["SUBREGIMEN", "DECLARACION DE LA MERCADERIA"]
            text_upper = text_content.upper()
            missing_keywords = [kw for kw in required_keywords if kw not in text_upper]

            if missing_keywords:
                # Eliminar archivo si la validación falla
                if file_path.exists():
                    os.remove(file_path)
                raise HTTPException(
                    status_code=400,
                    detail=f"El documento no parece ser un documento provisorio. Faltan las siguientes palabras clave: {', '.join(missing_keywords)}"
                )

            # Convertir PDF a imágenes B&N 300 DPI y guardar en la base de datos
            if file_extension == ".pdf":
                logger.info("Convirtiendo PDF a imágenes B&N 300 DPI")
                try:
                    images_data = pdf_to_image_service.pdf_to_bw_images(str(file_path), dpi=300)
                    logger.info(f"Se generaron {len(images_data)} imágenes del PDF")
                except Exception as e:
                    logger.error(f"Error convirtiendo PDF a imágenes: {str(e)}\n{traceback.format_exc()}")
                    if file_path.exists():
                        os.remove(file_path)
                    raise HTTPException(status_code=500, detail=f"Error convirtiendo PDF a imágenes: {str(e)}")
            else:
                # Para imágenes directas, convertir a B&N
                logger.info("Convirtiendo imagen a B&N 300 DPI")
                from PIL import Image
                from io import BytesIO
                try:
                    img = Image.open(str(file_path))
                    grayscale_img = img.convert('L')
                    bw_img = grayscale_img.convert('1')

                    img_byte_arr = BytesIO()
                    bw_img.save(img_byte_arr, format='PNG')
                    img_bytes = img_byte_arr.getvalue()
                    width, height = bw_img.size

                    images_data = [(img_bytes, width, height)]
                except Exception as e:
                    logger.error(f"Error convirtiendo imagen: {str(e)}\n{traceback.format_exc()}")
                    if file_path.exists():
                        os.remove(file_path)
                    raise HTTPException(status_code=500, detail=f"Error convirtiendo imagen: {str(e)}")

            extracted_data = {}
            # Extraer datos estructurados según método configurado (asumiendo que es una factura genérica)
            document_type = "document"
            if settings.EXTRACTION_METHOD == "vision":
                logger.info(f"Usando extracción basada en visión para documento provisorio")
                extraction_model_used = settings.VISION_MODEL
                if file_extension == ".pdf":
                    pass
                    #extracted_data, extraction_prompt = vision_service.extract_from_pdf(str(file_path), document_type, db)
                else:
                    pass
                    #extracted_data, extraction_prompt = vision_service.extract_from_image_file(str(file_path), document_type, db)
            else:
                logger.info(f"Usando extracción basada en OCR para documento provisorio")
                extraction_model_used = settings.OLLAMA_MODEL
                extraction_prompt = ""
                #extracted_data, extraction_prompt = llama_service.extract_structured_data(text_content, document_type, db)

            logger.info("Guardando documento provisorio y sus imágenes en la base de datos")
            # Guardar documento en base de datos
            db_document = ProvisionalDocument(
                filename=file.filename,
                file_path=str(file_path),
                reference=reference,
                extraction_model=extraction_model_used,
                extraction_prompt=extraction_prompt,
                extracted_data=extracted_data,
                text_content=text_content
            )

            db.add(db_document)
            db.flush()  # Para obtener el ID del documento

            # Guardar imágenes en la base de datos
            for page_num, (img_bytes, width, height) in enumerate(images_data, start=1):
                db_image = ProvisionalDocumentImage(
                    provisional_document_id=db_document.id,
                    page_number=page_num,
                    image_data=img_bytes,
                    width=width,
                    height=height
                )
                db.add(db_image)

            db.commit()
            db.refresh(db_document)

            return UploadResponse(
                message="Documento provisorio subido y procesado exitosamente",
                document_id=db_document.id,
                filename=file.filename,
                extracted_data=extracted_data
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error procesando documento provisional: {str(e)}\n{traceback.format_exc()}")
            db.rollback()
            # Eliminar archivo si hubo error
            if file_path.exists():
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_provisional_document: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/commercial", response_model=List[CommercialDocumentResponse])
async def list_commercial_documents(
    skip: int = 0,
    limit: int = 100,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lista todos los documentos comerciales"""
    try:
        query = db.query(CommercialDocument)

        if document_type:
            query = query.filter(CommercialDocument.document_type == document_type)

        documents = query.offset(skip).limit(limit).all()
        return documents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando documentos comerciales: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/commercial/{document_id}", response_model=CommercialDocumentResponse)
async def get_commercial_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un documento comercial específico"""
    try:
        document = db.query(CommercialDocument).filter(CommercialDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo documento comercial {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/provisional", response_model=List[ProvisionalDocumentResponse])
async def list_provisional_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista todos los documentos provisorios"""
    try:
        documents = db.query(ProvisionalDocument).offset(skip).limit(limit).all()
        return documents

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listando documentos provisorios: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/provisional/{document_id}", response_model=ProvisionalDocumentResponse)
async def get_provisional_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene un documento provisorio específico"""
    try:
        document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        return document

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo documento provisorio {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/commercial/{document_id}")
async def delete_commercial_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un documento comercial"""
    try:
        document = db.query(CommercialDocument).filter(CommercialDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        # Eliminar archivo físico
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        db.delete(document)
        db.commit()

        return {"message": "Documento eliminado exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando documento comercial {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/provisional/{document_id}")
async def delete_provisional_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Elimina un documento provisorio"""
    try:
        document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        # Eliminar archivo físico
        if os.path.exists(document.file_path):
            os.remove(document.file_path)

        db.delete(document)
        db.commit()

        return {"message": "Documento eliminado exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando documento provisorio {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/commercial/{document_id}/content")
async def get_commercial_document_content(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene el contenido de texto extraído de un documento comercial"""
    try:
        document = db.query(CommercialDocument).filter(CommercialDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        return {
            "document_id": document.id,
            "filename": document.filename,
            "document_type": document.document_type,
            "text_content": document.text_content or "No hay contenido de texto disponible"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo contenido de documento comercial {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/provisional/{document_id}/content")
async def get_provisional_document_content(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene el contenido de texto extraído de un documento provisorio"""
    try:
        document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        return {
            "document_id": document.id,
            "filename": document.filename,
            "text_content": document.text_content or "No hay contenido de texto disponible"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo contenido de documento provisorio {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/provisional/{document_id}/images")
async def get_provisional_document_images(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene información de las imágenes de un documento provisorio"""
    try:
        document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        images = db.query(ProvisionalDocumentImage).filter(
            ProvisionalDocumentImage.provisional_document_id == document_id
        ).order_by(ProvisionalDocumentImage.page_number).all()

        return {
            "document_id": document.id,
            "filename": document.filename,
            "total_pages": len(images),
            "images": [
                {
                    "id": img.id,
                    "page_number": img.page_number,
                    "width": img.width,
                    "height": img.height,
                    "created_at": img.created_at
                }
                for img in images
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo imágenes de documento provisorio {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/provisional/{document_id}/images/{page_number}")
async def get_provisional_document_image(
    document_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Obtiene una imagen específica de un documento provisorio"""
    try:
        from fastapi.responses import Response

        document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        image = db.query(ProvisionalDocumentImage).filter(
            ProvisionalDocumentImage.provisional_document_id == document_id,
            ProvisionalDocumentImage.page_number == page_number
        ).first()

        if not image:
            raise HTTPException(status_code=404, detail=f"Imagen de página {page_number} no encontrada")

        return Response(content=image.image_data, media_type="image/png")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo imagen de documento provisorio {document_id}, página {page_number}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/provisional/{document_id}/detect-pages")
async def detect_provisional_pages(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Detecta el tipo de página de todas las imágenes de un documento provisorio"""
    try:
        document = db.query(ProvisionalDocument).filter(ProvisionalDocument.id == document_id).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        detection_service = PageTypeDetectionService(db)
        results = detection_service.detect_document_pages(document_id)

        return {
            "document_id": document_id,
            "filename": document.filename,
            "pages": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detectando páginas de documento provisorio {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
