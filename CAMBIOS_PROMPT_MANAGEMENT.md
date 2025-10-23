# Resumen de Cambios - Sistema de Gestión de Prompts

## Descripción

Se ha implementado un sistema completo de gestión de prompts que permite administrar dinámicamente los prompts utilizados para clasificar documentos y extraer datos estructurados, sin necesidad de modificar el código.

## Archivos Modificados

### 1. `/backend/app/models/document.py`
**Cambios:**
- Agregado nuevo modelo `PromptTemplate` para almacenar prompts en la base de datos
- Campos: id, name, prompt_type, document_type, prompt_template, description, is_active, variables, created_at, updated_at

### 2. `/backend/app/schemas/document.py`
**Cambios:**
- Agregados schemas para prompts:
  - `PromptTemplateBase`: Schema base
  - `PromptTemplateCreate`: Para crear prompts
  - `PromptTemplateUpdate`: Para actualizar prompts
  - `PromptTemplateResponse`: Para respuestas de la API

### 3. `/backend/app/services/llama_service.py`
**Cambios:**
- Modificada función `classify_document()` para aceptar parámetro `db: Session`
- Ahora obtiene el prompt de clasificación desde la base de datos
- Incluye fallback al prompt hardcodeado si no hay uno en BD
- Modificada función `extract_structured_data()` para aceptar parámetro `db: Session`
- Ahora obtiene prompts de extracción específicos por tipo de documento desde BD
- Incluye fallback a prompts hardcodeados si no hay uno en BD

### 4. `/backend/app/api/routes/documents.py`
**Cambios:**
- Actualizado para pasar sesión de BD a `llama_service.classify_document()`
- Actualizado para pasar sesión de BD a `llama_service.extract_structured_data()`
- Modificadas líneas 63 y 68 (documento comercial)
- Modificada línea 137 (documento provisional)

### 5. `/backend/app/main.py`
**Cambios:**
- Importado `SessionLocal` y `PromptService`
- Importado router de prompts
- Agregada función `init_default_data()` para inicializar prompts al inicio
- Agregado router de prompts en `/api/v1/prompts`
- Actualizada descripción de la API para incluir gestión de prompts

## Archivos Nuevos

### 1. `/backend/app/services/prompt_service.py`
**Descripción:** Servicio completo para gestión de prompts (CRUD)

**Funciones principales:**
- `create_prompt()`: Crear nuevo prompt
- `get_prompt_by_id()`: Obtener por ID
- `get_prompt_by_name()`: Obtener por nombre
- `get_all_prompts()`: Listar todos
- `get_prompts_by_type()`: Filtrar por tipo
- `get_classification_prompt()`: Obtener prompt de clasificación activo
- `get_extraction_prompt()`: Obtener prompt de extracción activo por tipo de documento
- `update_prompt()`: Actualizar prompt
- `delete_prompt()`: Eliminar prompt
- `render_prompt()`: Renderizar template con variables
- `initialize_default_prompts()`: Inicializar prompts por defecto

### 2. `/backend/app/api/routes/prompts.py`
**Descripción:** Endpoints API completos para gestión de prompts

**Endpoints:**
- `POST /api/v1/prompts/` - Crear prompt
- `GET /api/v1/prompts/` - Listar prompts (con filtros)
- `GET /api/v1/prompts/{id}` - Obtener por ID
- `GET /api/v1/prompts/name/{name}` - Obtener por nombre
- `PUT /api/v1/prompts/{id}` - Actualizar prompt
- `DELETE /api/v1/prompts/{id}` - Eliminar prompt
- `POST /api/v1/prompts/initialize-defaults` - Inicializar prompts por defecto
- `GET /api/v1/prompts/classification/active` - Obtener clasificación activa
- `GET /api/v1/prompts/extraction/{type}/active` - Obtener extracción activa por tipo

### 3. `/PROMPT_MANAGEMENT.md`
**Descripción:** Documentación completa del sistema de gestión de prompts

**Contenido:**
- Descripción general del sistema
- Tipos de prompts (classification y extraction)
- Documentación de todos los endpoints API
- Ejemplos de uso para cada caso común
- Variables de template disponibles
- Buenas prácticas
- Estructura de base de datos
- Flujo de procesamiento
- Solución de problemas

### 4. `/examples/prompt_management_example.py`
**Descripción:** Script de ejemplo con casos de uso comunes

**Ejemplos incluidos:**
- Inicializar prompts por defecto
- Listar prompts (todos, por tipo, solo activos)
- Obtener prompts activos
- Crear prompt personalizado
- Actualizar prompt existente
- Obtener prompt por nombre
- Modificar prompt de clasificación

## Características Implementadas

### 1. Gestión Completa de Prompts
- CRUD completo (Create, Read, Update, Delete)
- Búsqueda por ID, nombre, tipo
- Filtrado por tipo y estado activo
- Versionado mediante nombres descriptivos

### 2. Sistema de Templates
- Variables dinámicas: `{text_content}`, `{document_type}`
- Renderizado automático de templates
- Validación de variables

### 3. Prompts por Defecto
- Inicialización automática al arrancar la aplicación
- 1 prompt de clasificación
- 6 prompts de extracción (uno por cada tipo de documento)
- Tipos soportados: factura, orden_compra, certificado_origen, especificacion_tecnica, contrato, remito

### 4. Activación/Desactivación
- Campo `is_active` para controlar qué prompt se usa
- Solo un prompt activo por tipo/documento
- Permite tener múltiples versiones y alternar entre ellas

### 5. Backward Compatibility
- Los prompts hardcodeados siguen funcionando como fallback
- Si no hay prompts en BD, usa los del código
- Migración gradual sin romper funcionalidad existente

### 6. Documentación y Ejemplos
- Documentación completa en PROMPT_MANAGEMENT.md
- Script de ejemplo con casos de uso reales
- Comentarios en el código

## Tipos de Documentos Soportados

1. **factura**: Facturas comerciales
2. **orden_compra**: Órdenes de compra
3. **certificado_origen**: Certificados de origen
4. **especificacion_tecnica**: Especificaciones técnicas
5. **contrato**: Contratos
6. **remito**: Remitos

Cada tipo tiene su propio prompt de extracción personalizable.

## Flujo de Uso

### Primera Vez (Automático)
1. Al iniciar la aplicación, se crean automáticamente las tablas de BD
2. Se inicializan los prompts por defecto
3. El sistema está listo para usar

### Personalización
1. Usuario consulta prompts actuales: `GET /api/v1/prompts/`
2. Usuario modifica un prompt: `PUT /api/v1/prompts/{id}`
3. El sistema usa automáticamente el nuevo prompt
4. Sin reiniciar la aplicación ni tocar código

### Procesamiento de Documentos
1. Usuario sube documento: `POST /api/v1/documents/commercial`
2. Sistema obtiene prompt de clasificación desde BD
3. Sistema clasifica el documento
4. Sistema obtiene prompt de extracción para ese tipo desde BD
5. Sistema extrae los datos
6. Retorna resultado al usuario

## Ventajas

1. **Sin modificar código**: Los prompts se gestionan vía API
2. **Versionado fácil**: Crear múltiples versiones y alternar
3. **Pruebas A/B**: Probar diferentes prompts sin despliegue
4. **Histórico**: Mantener versiones anteriores inactivas
5. **Flexibilidad**: Cada tipo de documento puede tener prompts únicos
6. **Backup automático**: Los prompts están en la BD
7. **API REST**: Integración fácil con interfaces de usuario
8. **Documentación**: Guías completas y ejemplos

## Próximos Pasos Sugeridos

1. **Interfaz de Usuario**: Crear UI para gestión visual de prompts
2. **Versionado Mejorado**: Sistema de versiones con git-like
3. **Métricas**: Tracking de performance por prompt
4. **A/B Testing**: Framework para comparar prompts
5. **Templates Compartidos**: Biblioteca de prompts de la comunidad
6. **Validación Avanzada**: Validación de formato de respuesta esperado
7. **Multi-idioma**: Prompts en diferentes idiomas
8. **Permisos**: Control de acceso a modificación de prompts

## Testing

Para probar la funcionalidad:

1. Iniciar la aplicación:
```bash
cd /home/user/corrector_despa/backend
uvicorn app.main:app --reload
```

2. Ejecutar script de ejemplo:
```bash
cd /home/user/corrector_despa
python examples/prompt_management_example.py
```

3. O usar la documentación interactiva:
```
http://localhost:8000/api/v1/docs
```

## Notas Técnicas

- **Base de Datos**: SQLAlchemy con SQLite
- **Framework**: FastAPI
- **ORM**: SQLAlchemy
- **Validación**: Pydantic
- **LLM**: Ollama con Phi-4

## Compatibilidad

- Compatible con la versión anterior
- No rompe funcionalidad existente
- Migración gradual recomendada
- Fallbacks automáticos

## Mantenimiento

- Los prompts están en BD, fáciles de respaldar
- Usar `initialize-defaults` solo una vez
- Modificar prompts vía API
- Mantener documentación actualizada cuando se agreguen nuevos tipos
