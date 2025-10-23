from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from .core.config import settings
from .core.database import engine, Base
from .api.routes import documents, comparisons, attributes

# Configurar zona horaria
os.environ['TZ'] = 'America/Argentina/Buenos_Aires'

# Crear tablas en la base de datos
Base.metadata.create_all(bind=engine)

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

    ### Flujo de trabajo:

    1. Configura atributos con `/api/v1/attributes/defaults` (primera vez)
    2. Sube documentos comerciales usando `/api/v1/documents/commercial`
    3. Sube documentos provisorios usando `/api/v1/documents/provisional`
    4. Compara documentos usando `/api/v1/comparisons/` o `/api/v1/comparisons/batch`
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
