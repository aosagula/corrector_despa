from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import traceback

from ...core.database import get_db
from ...schemas.document import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse
)
from ...services.prompt_service import PromptService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=PromptTemplateResponse)
async def create_prompt(
    prompt_data: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Crea una nueva plantilla de prompt

    - **name**: Nombre único del prompt
    - **prompt_type**: "classification" o "extraction"
    - **document_type**: Tipo de documento (solo para extraction)
    - **prompt_template**: Template con variables como {text_content}, {document_type}
    - **description**: Descripción opcional
    - **is_active**: 1=activo, 0=inactivo
    - **variables**: Diccionario con las variables disponibles
    """
    try:
        # Verificar que no exista un prompt con el mismo nombre
        existing = PromptService.get_prompt_by_name(db, prompt_data.name)
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un prompt con ese nombre")

        # Validar que el prompt_type sea válido
        if prompt_data.prompt_type not in ["classification", "extraction"]:
            raise HTTPException(
                status_code=400,
                detail="prompt_type debe ser 'classification' o 'extraction'"
            )

        # Validar que extraction tenga document_type
        if prompt_data.prompt_type == "extraction" and not prompt_data.document_type:
            raise HTTPException(
                status_code=400,
                detail="Los prompts de tipo 'extraction' deben especificar un document_type"
            )

        return PromptService.create_prompt(db, prompt_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating prompt: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/", response_model=List[PromptTemplateResponse])
async def list_prompts(
    skip: int = 0,
    limit: int = 100,
    prompt_type: Optional[str] = None,
    active_only: bool = False,
    db: Session = Depends(get_db)
):
    """
    Lista todas las plantillas de prompts

    - **skip**: Número de registros a saltar
    - **limit**: Número máximo de registros a retornar
    - **prompt_type**: Filtrar por tipo (classification o extraction)
    - **active_only**: Solo prompts activos
    """
    try:
        if prompt_type:
            return PromptService.get_prompts_by_type(db, prompt_type, active_only)
        else:
            prompts = PromptService.get_all_prompts(db, skip, limit)
            if active_only:
                prompts = [p for p in prompts if p.is_active == 1]
            return prompts
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing prompts: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/{prompt_id}", response_model=PromptTemplateResponse)
async def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Obtiene una plantilla de prompt específica por ID"""
    try:
        prompt = PromptService.get_prompt_by_id(db, prompt_id)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt no encontrado")
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt by ID {prompt_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/name/{prompt_name}", response_model=PromptTemplateResponse)
async def get_prompt_by_name(
    prompt_name: str,
    db: Session = Depends(get_db)
):
    """Obtiene una plantilla de prompt específica por nombre"""
    try:
        prompt = PromptService.get_prompt_by_name(db, prompt_name)
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt no encontrado")
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting prompt by name {prompt_name}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.put("/{prompt_id}", response_model=PromptTemplateResponse)
async def update_prompt(
    prompt_id: int,
    prompt_data: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    Actualiza una plantilla de prompt existente

    Permite actualizar cualquier campo del prompt.
    Solo se actualizarán los campos proporcionados.
    """
    try:
        # Verificar que el prompt existe
        existing = PromptService.get_prompt_by_id(db, prompt_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Prompt no encontrado")

        # Si se está cambiando el nombre, verificar que no exista otro con ese nombre
        if prompt_data.name and prompt_data.name != existing.name:
            other = PromptService.get_prompt_by_name(db, prompt_data.name)
            if other:
                raise HTTPException(status_code=400, detail="Ya existe un prompt con ese nombre")

        # Validar prompt_type si se está actualizando
        if prompt_data.prompt_type and prompt_data.prompt_type not in ["classification", "extraction"]:
            raise HTTPException(
                status_code=400,
                detail="prompt_type debe ser 'classification' o 'extraction'"
            )

        updated_prompt = PromptService.update_prompt(db, prompt_id, prompt_data)
        return updated_prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompt {prompt_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.delete("/{prompt_id}")
async def delete_prompt(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Elimina una plantilla de prompt"""
    try:
        success = PromptService.delete_prompt(db, prompt_id)
        if not success:
            raise HTTPException(status_code=404, detail="Prompt no encontrado")

        return {"message": "Prompt eliminado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt {prompt_id}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.post("/initialize-defaults")
async def initialize_default_prompts(
    db: Session = Depends(get_db)
):
    """
    Inicializa los prompts por defecto en la base de datos

    Este endpoint carga los prompts predefinidos para clasificación
    y extracción de datos. Solo carga prompts si la tabla está vacía.
    """
    try:
        PromptService.initialize_default_prompts(db)
        return {"message": "Prompts por defecto inicializados exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing default prompts: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/classification/active", response_model=PromptTemplateResponse)
async def get_active_classification_prompt(
    db: Session = Depends(get_db)
):
    """Obtiene el prompt activo de clasificación"""
    try:
        prompt = PromptService.get_classification_prompt(db)
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail="No hay un prompt de clasificación activo. Use /initialize-defaults para crear los prompts por defecto."
            )
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active classification prompt: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/extraction/{document_type}/active", response_model=PromptTemplateResponse)
async def get_active_extraction_prompt(
    document_type: str,
    db: Session = Depends(get_db)
):
    """Obtiene el prompt activo de extracción para un tipo de documento específico"""
    try:
        prompt = PromptService.get_extraction_prompt(db, document_type)
        if not prompt:
            raise HTTPException(
                status_code=404,
                detail=f"No hay un prompt de extracción activo para el tipo '{document_type}'. Use /initialize-defaults para crear los prompts por defecto."
            )
        return prompt
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting active extraction prompt for {document_type}: {str(e)}\n{traceback.format_exc()}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
