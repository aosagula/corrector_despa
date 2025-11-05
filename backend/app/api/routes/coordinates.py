from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import logging
import traceback

from ...core.database import get_db

logger = logging.getLogger(__name__)
from ...models.document import (
    AttributeExtractionCoordinate,
    ConfigurableAttribute,
    ProvisionalDocument,
    ProvisionalDocumentImage
)
from ...schemas.coordinate import (
    CoordinateCreate,
    CoordinateUpdate,
    CoordinateResponse
)
from ...services.coordinate_extraction_service import coordinate_extraction_service

router = APIRouter()


@router.post("/", response_model=CoordinateResponse)
async def create_coordinate(
    coordinate: CoordinateCreate,
    db: Session = Depends(get_db)
):
    """Crea una nueva coordenada de extracción para un atributo"""
    try:
        # Verificar que el atributo existe
        attribute = db.query(ConfigurableAttribute).filter(
            ConfigurableAttribute.id == coordinate.attribute_id
        ).first()

        if not attribute:
            raise HTTPException(status_code=404, detail="Atributo no encontrado")

        db_coordinate = AttributeExtractionCoordinate(**coordinate.dict())
        db.add(db_coordinate)
        db.commit()
        db.refresh(db_coordinate)

        return db_coordinate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating coordinate: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=List[CoordinateResponse])
async def list_coordinates(
    attribute_id: int = None,
    page_type_id: int = None,
    db: Session = Depends(get_db)
):
    """Lista todas las coordenadas de extracción, opcionalmente filtradas por atributo o tipo de página"""
    try:
        query = db.query(AttributeExtractionCoordinate)

        if attribute_id:
            query = query.filter(AttributeExtractionCoordinate.attribute_id == attribute_id)

        if page_type_id:
            query = query.filter(AttributeExtractionCoordinate.page_type_id == page_type_id)

        coordinates = query.all()
        return coordinates

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing coordinates: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{coordinate_id}", response_model=CoordinateResponse)
async def get_coordinate(
    coordinate_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una coordenada específica"""
    try:
        coordinate = db.query(AttributeExtractionCoordinate).filter(
            AttributeExtractionCoordinate.id == coordinate_id
        ).first()

        if not coordinate:
            raise HTTPException(status_code=404, detail="Coordenada no encontrada")

        return coordinate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coordinate {coordinate_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{coordinate_id}", response_model=CoordinateResponse)
async def update_coordinate(
    coordinate_id: int,
    coordinate_update: CoordinateUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza una coordenada existente"""
    try:
        db_coordinate = db.query(AttributeExtractionCoordinate).filter(
            AttributeExtractionCoordinate.id == coordinate_id
        ).first()

        if not db_coordinate:
            raise HTTPException(status_code=404, detail="Coordenada no encontrada")

        update_data = coordinate_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_coordinate, key, value)

        db.commit()
        db.refresh(db_coordinate)

        return db_coordinate

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating coordinate {coordinate_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/{coordinate_id}")
async def delete_coordinate(
    coordinate_id: int,
    db: Session = Depends(get_db)
):
    """Elimina una coordenada"""
    try:
        db_coordinate = db.query(AttributeExtractionCoordinate).filter(
            AttributeExtractionCoordinate.id == coordinate_id
        ).first()

        if not db_coordinate:
            raise HTTPException(status_code=404, detail="Coordenada no encontrada")

        db.delete(db_coordinate)
        db.commit()

        return {"message": "Coordenada eliminada exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting coordinate {coordinate_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/extract/{document_id}")
async def extract_data_by_coordinates(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Extrae datos de un documento provisorio usando las coordenadas configuradas
    para cada tipo de página. Primero detecta el tipo de cada página y luego
    aplica las coordenadas correspondientes a ese tipo.
    """
    try:
        # Obtener documento
        document = db.query(ProvisionalDocument).filter(
            ProvisionalDocument.id == document_id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        # Obtener imágenes del documento
        images = db.query(ProvisionalDocumentImage).filter(
            ProvisionalDocumentImage.provisional_document_id == document_id
        ).order_by(ProvisionalDocumentImage.page_number).all()

        if not images:
            raise HTTPException(status_code=404, detail="No hay imágenes para este documento")

        # Primero detectar el tipo de cada página
        from ...services.page_type_detection_service import PageTypeDetectionService
        detection_service = PageTypeDetectionService(db)
        page_detection_results = detection_service.detect_document_pages(document_id)

        # Agrupar coordenadas por tipo de página
        coordinates_by_page_type = {}
        all_coordinates = db.query(AttributeExtractionCoordinate).all()

        for coord in all_coordinates:
            if coord.page_type_id not in coordinates_by_page_type:
                coordinates_by_page_type[coord.page_type_id] = []

            coordinates_by_page_type[coord.page_type_id].append({
                'label': coord.label,
                'data_type': coord.data_type if hasattr(coord, 'data_type') else 'text',
                'x1': coord.x1,
                'y1': coord.y1,
                'x2': coord.x2,
                'y2': coord.y2
            })

        # Ahora mapear las coordenadas a cada página según su tipo detectado
        coordinates_by_page = {}
        for page_result in page_detection_results:
            page_num = page_result['page_number']
            detected_type = page_result['detected_type']

            if detected_type and detected_type['page_type_id'] in coordinates_by_page_type:
                coordinates_by_page[page_num] = coordinates_by_page_type[detected_type['page_type_id']]
            else:
                coordinates_by_page[page_num] = []

        # Preparar datos de imágenes
        images_data = [
            (img.image_data, img.width, img.height)
            for img in images
        ]

        # Extraer datos
        extracted_data = coordinate_extraction_service.extract_from_document_images(
            images_data,
            coordinates_by_page
        )

        return {
            "document_id": document_id,
            "filename": document.filename,
            "total_pages": len(images),
            "page_types_detected": page_detection_results,
            "extracted_data": extracted_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting data by coordinates for document {document_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
