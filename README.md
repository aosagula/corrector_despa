# Corrector de Documentos Comerciales

Sistema inteligente para clasificar y validar documentos comerciales utilizando IA (Phi-4 via Llama).

## Características

- **Clasificación automática** de documentos comerciales (facturas, órdenes de compra, certificados, etc.)
- **Extracción de datos** de PDFs e imágenes usando OCR (Tesseract)
- **Validación inteligente** comparando documentos provisorios con documentos comerciales
- **Atributos configurables** para personalizar las comparaciones
- **Interfaz web moderna** con Bootstrap 5
- **API REST completa** con documentación automática (FastAPI)
- **Arquitectura de contenedores** Docker para fácil despliegue

## Arquitectura

```
┌─────────────────┐
│   Frontend      │  Nginx + HTML + Bootstrap + JavaScript
│   (Puerto 80)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend       │  FastAPI + Python
│   (Puerto 8000) │
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────┐
    ▼         ▼            ▼          ▼
┌────────┐ ┌──────┐  ┌─────────┐ ┌────────┐
│MariaDB │ │Ollama│  │Tesseract│ │PDF2Img │
│ (3306) │ │(Phi4)│  │  (OCR)  │ │        │
└────────┘ │11434 │  └─────────┘ └────────┘
           └──────┘
```

## Requisitos

- Docker y Docker Compose
- Al menos 8GB de RAM (Phi-4 requiere recursos significativos)
- 20GB de espacio en disco

## Instalación y Despliegue Local

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd corrector_despa
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env según tus necesidades
```

### 3. Iniciar los servicios

```bash
docker-compose up -d
```

### 4. Descargar el modelo Phi-4 en Ollama

```bash
# Esperar a que Ollama esté listo (puede tomar unos minutos)
docker exec -it corrector_ollama ollama pull phi4
```

**Nota:** La descarga del modelo Phi-4 puede tomar varios minutos dependiendo de tu conexión a internet (el modelo pesa varios GB).

### 5. Acceder a la aplicación

- **Frontend:** http://localhost
- **API Documentation:** http://localhost:8000/api/v1/docs
- **API ReDoc:** http://localhost:8000/api/v1/redoc

### 6. Configurar atributos iniciales

1. Ve a la sección "Configurar Atributos" en la interfaz web
2. Haz clic en "Cargar Atributos por Defecto" para crear atributos predefinidos

## Uso

### 1. Subir Documentos Comerciales

1. Ve a la pestaña "Documentos Comerciales"
2. Selecciona un archivo (PDF, PNG, JPG)
3. El sistema automáticamente:
   - Extraerá el texto del documento
   - Clasificará el tipo de documento
   - Extraerá datos estructurados

### 2. Subir Documento Provisorio

1. Ve a la pestaña "Documento Provisorio"
2. Sube el documento que deseas validar

### 3. Comparar Documentos

1. Ve a la pestaña "Comparar"
2. Selecciona un documento comercial y uno provisorio
3. Haz clic en "Comparar" para comparación individual
4. O haz clic en "Comparar con Todos" para validar contra todos los documentos comerciales

### 4. Configurar Atributos

Define qué campos se deben comparar entre documentos:

- **Nombre del Atributo:** Nombre descriptivo
- **Clave en JSON:** Nombre del campo en los datos extraídos (ej: `monto_total`, `fecha`)
- **Tipo de Validación:** Texto, Numérico, o Fecha
- **Campo Requerido:** Si el campo debe estar presente obligatoriamente

## API Endpoints

### Documentos Comerciales

- `POST /api/v1/documents/commercial` - Subir documento comercial
- `GET /api/v1/documents/commercial` - Listar documentos comerciales
- `GET /api/v1/documents/commercial/{id}` - Obtener documento específico
- `DELETE /api/v1/documents/commercial/{id}` - Eliminar documento

### Documentos Provisorios

- `POST /api/v1/documents/provisional` - Subir documento provisorio
- `GET /api/v1/documents/provisional` - Listar documentos provisorios
- `GET /api/v1/documents/provisional/{id}` - Obtener documento específico
- `DELETE /api/v1/documents/provisional/{id}` - Eliminar documento

### Comparaciones

- `POST /api/v1/comparisons/` - Crear comparación entre dos documentos
- `POST /api/v1/comparisons/batch?provisional_document_id={id}` - Comparar provisorio con todos
- `GET /api/v1/comparisons/` - Listar comparaciones
- `GET /api/v1/comparisons/{id}` - Obtener comparación específica

### Atributos Configurables

- `POST /api/v1/attributes/` - Crear atributo
- `GET /api/v1/attributes/` - Listar atributos
- `GET /api/v1/attributes/{id}` - Obtener atributo específico
- `PUT /api/v1/attributes/{id}` - Actualizar atributo
- `DELETE /api/v1/attributes/{id}` - Eliminar atributo
- `POST /api/v1/attributes/defaults` - Crear atributos por defecto

## Despliegue en Railway

Railway es una plataforma de despliegue que soporta Docker y puede alojar toda tu aplicación.

### Opción 1: Usando Railway CLI

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login
railway login

# Crear nuevo proyecto
railway init

# Desplegar
railway up
```

### Opción 2: Desde el repositorio de GitHub

1. Conecta tu repositorio a Railway
2. Railway detectará automáticamente el `docker-compose.yml`
3. Configura las variables de entorno en el dashboard de Railway
4. Despliega

### Configuración importante para Railway:

**Variables de entorno necesarias:**

```
DB_ROOT_PASSWORD=tu_password_segura
DB_NAME=corrector_despa
DB_USER=corrector
DB_PASSWORD=tu_password_db
OLLAMA_MODEL=phi4
```

**Notas sobre Railway:**

1. **Base de datos:** Railway ofrece MariaDB/MySQL como plugin. Úsalo en lugar del contenedor de DB.
2. **Persistencia:** Configura volúmenes para `uploads` y datos de Ollama.
3. **Memoria:** Asegúrate de que tu plan tenga suficiente RAM para Phi-4 (mínimo 8GB recomendado).
4. **Modelo Phi-4:** Después del despliegue, ejecuta `ollama pull phi4` en el contenedor de Ollama.

### Comando para descargar Phi-4 en Railway:

```bash
railway run docker exec corrector_ollama ollama pull phi4
```

## Despliegue en Otros Proveedores

### Render

1. Conecta tu repositorio de GitHub
2. Crea un nuevo Blueprint con `docker-compose.yml`
3. Configura las variables de entorno
4. Despliega

### DigitalOcean App Platform

1. Sube tu aplicación desde GitHub
2. DigitalOcean detectará Docker Compose
3. Configura componentes individuales
4. Despliega

### Google Cloud Run

1. Build containers: `docker-compose build`
2. Push a Google Container Registry
3. Despliega en Cloud Run
4. Configura Cloud SQL para la base de datos

## Desarrollo

### Estructura del Proyecto

```
corrector_despa/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── documents.py
│   │   │       ├── comparisons.py
│   │   │       └── attributes.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   └── document.py
│   │   ├── schemas/
│   │   │   └── document.py
│   │   ├── services/
│   │   │   ├── llama_service.py
│   │   │   ├── ocr_service.py
│   │   │   └── comparison_service.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── config.js
│   │   ├── api.js
│   │   └── app.js
│   ├── index.html
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

### Ejecutar en modo desarrollo

```bash
# Backend con hot-reload
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
# Servir con cualquier servidor HTTP
python -m http.server 3000
```

## Solución de Problemas

### El modelo Phi-4 no responde

```bash
# Verificar que Ollama esté corriendo
docker ps | grep ollama

# Ver logs de Ollama
docker logs corrector_ollama

# Reinstalar modelo
docker exec -it corrector_ollama ollama pull phi4
```

### Error de OCR en PDFs

```bash
# Verificar que Tesseract esté instalado en el contenedor
docker exec -it corrector_backend tesseract --version

# Verificar idiomas disponibles
docker exec -it corrector_backend tesseract --list-langs
```

### Problemas de conexión a la base de datos

```bash
# Verificar que MariaDB esté corriendo
docker ps | grep mariadb

# Ver logs de la base de datos
docker logs corrector_db

# Conectar a la base de datos
docker exec -it corrector_db mysql -u corrector -p
```

### Problemas de memoria con Phi-4

Si Ollama se queda sin memoria:

1. Considera usar un modelo más pequeño (phi3, llama2:7b)
2. Aumenta la RAM disponible para Docker
3. Modifica `OLLAMA_MODEL` en `.env`

## Tecnologías Utilizadas

- **Backend:** Python 3.11, FastAPI, SQLAlchemy
- **Frontend:** HTML5, Bootstrap 5, JavaScript (Vanilla)
- **Base de Datos:** MariaDB 11.0
- **IA/ML:** Ollama (Phi-4), Tesseract OCR
- **Containerización:** Docker, Docker Compose
- **Servidor Web:** Nginx

## Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

Este proyecto está bajo la licencia MIT.

## Soporte

Para reportar problemas o sugerencias, abre un issue en el repositorio.

## Roadmap

- [ ] Autenticación de usuarios
- [ ] Exportación de reportes en PDF
- [ ] Integración con sistemas ERP
- [ ] Soporte para más tipos de documentos
- [ ] API webhooks para notificaciones
- [ ] Dashboard con métricas y estadísticas
- [ ] Soporte multi-idioma
- [ ] Modo offline para el OCR
