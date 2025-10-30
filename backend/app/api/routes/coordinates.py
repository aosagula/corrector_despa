from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from ...core.database import get_db
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


@router.get("/", response_model=List[CoordinateResponse])
async def list_coordinates(
    attribute_id: int = None,
    page_number: int = None,
    db: Session = Depends(get_db)
):
    """Lista todas las coordenadas de extracción, opcionalmente filtradas por atributo o página"""
    query = db.query(AttributeExtractionCoordinate)

    if attribute_id:
        query = query.filter(AttributeExtractionCoordinate.attribute_id == attribute_id)

    if page_number:
        query = query.filter(AttributeExtractionCoordinate.page_number == page_number)

    coordinates = query.all()
    return coordinates


@router.get("/{coordinate_id}", response_model=CoordinateResponse)
async def get_coordinate(
    coordinate_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una coordenada específica"""
    coordinate = db.query(AttributeExtractionCoordinate).filter(
        AttributeExtractionCoordinate.id == coordinate_id
    ).first()

    if not coordinate:
        raise HTTPException(status_code=404, detail="Coordenada no encontrada")

    return coordinate


@router.put("/{coordinate_id}", response_model=CoordinateResponse)
async def update_coordinate(
    coordinate_id: int,
    coordinate_update: CoordinateUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza una coordenada existente"""
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


@router.delete("/{coordinate_id}")
async def delete_coordinate(
    coordinate_id: int,
    db: Session = Depends(get_db)
):
    """Elimina una coordenada"""
    db_coordinate = db.query(AttributeExtractionCoordinate).filter(
        AttributeExtractionCoordinate.id == coordinate_id
    ).first()

    if not db_coordinate:
        raise HTTPException(status_code=404, detail="Coordenada no encontrada")

    db.delete(db_coordinate)
    db.commit()

    return {"message": "Coordenada eliminada exitosamente"}


@router.post("/extract/{document_id}")
async def extract_data_by_coordinates(
    document_id: int,
    db: Session = Depends(get_db)
) -> Dict:
    """
    Extrae datos de un documento provisorio usando las coordenadas configuradas
    para cada atributo
    """
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

    # Obtener todas las coordenadas configuradas
    coordinates = db.query(AttributeExtractionCoordinate).all()

    if not coordinates:
        raise HTTPException(status_code=404, detail="No hay coordenadas de extracción configuradas")

    # Agrupar coordenadas por página
    coordinates_by_page = {}
    for coord in coordinates:
        if coord.page_number not in coordinates_by_page:
            coordinates_by_page[coord.page_number] = []

        coordinates_by_page[coord.page_number].append({
            'label': coord.label,
            'x1': coord.x1,
            'y1': coord.y1,
            'x2': coord.x2,
            'y2': coord.y2
        })

    # Preparar datos de imágenes
    images_data = [
        (img.image_data, img.width, img.height)
        for img in images
    ]

    # Extraer datos
    try:
        extracted_data = coordinate_extraction_service.extract_from_document_images(
            images_data,
            coordinates_by_page
        )

        return {
            "document_id": document_id,
            "filename": document.filename,
            "total_pages": len(images),
            "extracted_data": extracted_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extrayendo datos: {str(e)}")
