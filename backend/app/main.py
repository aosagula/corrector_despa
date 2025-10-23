from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import logging

from .core.config import settings
from .core.database import engine, Base, SessionLocal
from .api.routes import documents, comparisons, attributes, prompts
from .services.prompt_service import PromptService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configurar zona horaria
os.environ['TZ'] = 'America/Argentina/Buenos_Aires'

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Inicializar prompts por defecto
def init_default_data():
    """Inicializa datos por defecto en la base de datos"""
    db = SessionLocal()
    try:
        PromptService.initialize_default_prompts(db)
    except Exception as e:
        print(f"Error inicializando prompts por defecto: {e}")
    finally:
        db.close()

init_default_data()

# Crear aplicación FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## API de Corrector de Documentos Comerciales

    Sistema completo de clasificación, validación y comparación de documentos comerciales usando IA.

    ### Características principales:

    * **Documentos Comerciales**: Sube y procesa documentos con clasificación automática usando Phi-4
    * **Documentos Provisorios**: Sube documentos para validar contra los comerciales
    * **Comparaciones**: Compara documentos y valida atributos configurables
    * **Atributos Configurables**: Define qué campos comparar y sus reglas de validación
    * **Prompts Administrables**: Gestiona y personaliza los prompts de clasificación y extracción

    ### Flujo de trabajo:

    1. Inicializa prompts por defecto con `/api/v1/prompts/initialize-defaults` (primera vez)
    2. Configura atributos con `/api/v1/attributes/defaults` (primera vez)
    3. Sube documentos comerciales usando `/api/v1/documents/commercial`
    4. Sube documentos provisorios usando `/api/v1/documents/provisional`
    5. Compara documentos usando `/api/v1/comparisons/` o `/api/v1/comparisons/batch`
    6. Personaliza prompts según tus necesidades con `/api/v1/prompts/`
    """,
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(
    documents.router,
    prefix=f"{settings.API_V1_STR}/documents",
    tags=["documents"]
)

app.include_router(
    comparisons.router,
    prefix=f"{settings.API_V1_STR}/comparisons",
    tags=["comparisons"]
)

app.include_router(
    attributes.router,
    prefix=f"{settings.API_V1_STR}/attributes",
    tags=["attributes"]
)

app.include_router(
    prompts.router,
    prefix=f"{settings.API_V1_STR}/prompts",
    tags=["prompts"]
)


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "API de Corrector de Documentos",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
