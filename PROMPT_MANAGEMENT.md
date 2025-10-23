# Gestión de Prompts

Esta aplicación ahora incluye un sistema completo de gestión de prompts que permite personalizar cómo se clasifican y extraen datos de los documentos.

## Descripción General

El sistema de prompts permite:
- Personalizar el prompt usado para clasificar documentos
- Personalizar los prompts de extracción de datos según el tipo de documento
- Modificar y versionar prompts sin tocar el código
- Activar/desactivar prompts según necesidad

## Tipos de Prompts

### 1. Prompts de Clasificación (classification)
Estos prompts se usan para determinar el tipo de documento (factura, orden de compra, etc.).

**Características:**
- Solo puede haber un prompt de clasificación activo a la vez
- El `document_type` debe ser `null` para estos prompts
- Variables disponibles: `{text_content}`

### 2. Prompts de Extracción (extraction)
Estos prompts se usan para extraer datos estructurados de cada tipo de documento.

**Características:**
- Cada tipo de documento debe tener su propio prompt
- El `document_type` especifica para qué tipo de documento es el prompt
- Variables disponibles: `{text_content}`, `{document_type}`

## API Endpoints

### Inicializar Prompts por Defecto
```bash
POST /api/v1/prompts/initialize-defaults
```
Carga los prompts predefinidos en la base de datos. Solo se ejecuta si la tabla está vacía.

**Respuesta:**
```json
{
  "message": "Prompts por defecto inicializados exitosamente"
}
```

### Listar Todos los Prompts
```bash
GET /api/v1/prompts/
```

**Parámetros de consulta:**
- `skip`: Número de registros a saltar (default: 0)
- `limit`: Número máximo de registros (default: 100)
- `prompt_type`: Filtrar por tipo ("classification" o "extraction")
- `active_only`: Solo prompts activos (default: false)

**Ejemplo:**
```bash
GET /api/v1/prompts/?prompt_type=extraction&active_only=true
```

### Obtener Prompt por ID
```bash
GET /api/v1/prompts/{prompt_id}
```

### Obtener Prompt por Nombre
```bash
GET /api/v1/prompts/name/{prompt_name}
```

### Obtener Prompt de Clasificación Activo
```bash
GET /api/v1/prompts/classification/active
```

### Obtener Prompt de Extracción Activo para un Tipo
```bash
GET /api/v1/prompts/extraction/{document_type}/active
```

**Ejemplo:**
```bash
GET /api/v1/prompts/extraction/factura/active
```

### Crear un Nuevo Prompt
```bash
POST /api/v1/prompts/
```

**Body (ejemplo para clasificación):**
```json
{
  "name": "my_custom_classification",
  "prompt_type": "classification",
  "document_type": null,
  "prompt_template": "Analiza este documento y clasifícalo:\n{text_content}\n\nResponde en formato JSON.",
  "description": "Mi prompt personalizado de clasificación",
  "is_active": 1,
  "variables": {
    "text_content": "Contenido del documento"
  }
}
```

**Body (ejemplo para extracción):**
```json
{
  "name": "extraction_factura_custom",
  "prompt_type": "extraction",
  "document_type": "factura",
  "prompt_template": "Extrae estos datos de la factura:\n{text_content}\n\nFormato JSON.",
  "description": "Extracción personalizada para facturas",
  "is_active": 1,
  "variables": {
    "text_content": "Contenido del documento",
    "document_type": "factura"
  }
}
```

### Actualizar un Prompt
```bash
PUT /api/v1/prompts/{prompt_id}
```

**Body (actualización parcial):**
```json
{
  "prompt_template": "Nuevo template del prompt con {text_content}",
  "description": "Descripción actualizada"
}
```

### Eliminar un Prompt
```bash
DELETE /api/v1/prompts/{prompt_id}
```

## Ejemplos de Uso

### Caso 1: Modificar el Prompt de Clasificación

1. Obtener el prompt actual:
```bash
GET /api/v1/prompts/classification/active
```

2. Copiar el ID del prompt y actualizarlo:
```bash
PUT /api/v1/prompts/1
{
  "prompt_template": "Tu nuevo prompt de clasificación personalizado con {text_content}"
}
```

### Caso 2: Crear un Nuevo Prompt de Extracción para un Tipo de Documento

```bash
POST /api/v1/prompts/
{
  "name": "extraction_contrato_v2",
  "prompt_type": "extraction",
  "document_type": "contrato",
  "prompt_template": "Extrae la siguiente información del contrato:\n\nTexto: {text_content}\n\nCampos requeridos:\n- numero_contrato\n- fecha\n- partes\n- clausulas_importantes\n- vigencia\n\nRespuesta en JSON.",
  "description": "Versión mejorada del prompt para contratos",
  "is_active": 1
}
```

### Caso 3: Desactivar un Prompt y Activar Otro

1. Desactivar el prompt actual:
```bash
PUT /api/v1/prompts/5
{
  "is_active": 0
}
```

2. Activar el nuevo prompt:
```bash
PUT /api/v1/prompts/6
{
  "is_active": 1
}
```

## Variables de Template

Los prompts usan un sistema de templates con variables. Las variables se especifican entre llaves `{}`.

### Variables Disponibles

**Para prompts de clasificación:**
- `{text_content}`: Contenido de texto del documento (primeros 3000 caracteres)

**Para prompts de extracción:**
- `{text_content}`: Contenido de texto del documento (primeros 4000 caracteres)
- `{document_type}`: Tipo de documento clasificado

### Ejemplo de Template

```
Analiza el siguiente documento de tipo "{document_type}":

{text_content}

Extrae los siguientes campos en formato JSON:
- numero
- fecha
- monto
```

Al procesarse, las variables serían reemplazadas:
```
Analiza el siguiente documento de tipo "factura":

[contenido del documento aquí]

Extrae los siguientes campos en formato JSON:
- numero
- fecha
- monto
```

## Buenas Prácticas

1. **Versionado**: Usa nombres descriptivos con versiones (ej: `extraction_factura_v2`)
2. **Descripción**: Siempre incluye una descripción clara del propósito del prompt
3. **Pruebas**: Prueba los nuevos prompts con documentos reales antes de activarlos
4. **Respaldo**: Antes de modificar un prompt, crea uno nuevo con el cambio
5. **Activación**: Solo un prompt de cada tipo/documento debe estar activo
6. **Variables**: Documenta las variables disponibles en el campo `variables`

## Tipos de Documentos Soportados

Los prompts por defecto soportan estos tipos de documentos:
- `factura`
- `orden_compra`
- `certificado_origen`
- `especificacion_tecnica`
- `contrato`
- `remito`
- `otro`

Puedes crear prompts de extracción para cualquiera de estos tipos.

## Estructura de Base de Datos

La tabla `prompt_templates` tiene la siguiente estructura:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | Integer | ID único |
| name | String(100) | Nombre único del prompt |
| prompt_type | String(50) | "classification" o "extraction" |
| document_type | String(100) | Tipo de documento (null para classification) |
| prompt_template | Text | Template del prompt con variables |
| description | Text | Descripción del prompt |
| is_active | Integer | 1=activo, 0=inactivo |
| variables | JSON | Diccionario de variables disponibles |
| created_at | DateTime | Fecha de creación |
| updated_at | DateTime | Fecha de última actualización |

## Flujo de Procesamiento

Cuando se sube un documento:

1. **Clasificación**:
   - Se obtiene el prompt de clasificación activo de la BD
   - Se renderiza el template con el contenido del documento
   - Se envía al modelo LLM (Phi-4)
   - Se obtiene el tipo de documento

2. **Extracción**:
   - Se obtiene el prompt de extracción activo para ese tipo de documento
   - Se renderiza el template con el contenido y tipo de documento
   - Se envía al modelo LLM (Phi-4)
   - Se obtienen los datos estructurados

## Solución de Problemas

**Error: "No hay un prompt de clasificación activo"**
- Ejecuta: `POST /api/v1/prompts/initialize-defaults`

**Error: "No hay un prompt de extracción activo para el tipo X"**
- Crea un prompt de extracción para ese tipo de documento
- O ejecuta `initialize-defaults` para cargar los prompts por defecto

**El prompt no se aplica**
- Verifica que `is_active` sea 1
- Verifica que no haya otro prompt activo del mismo tipo/documento
- Revisa los logs de la aplicación para ver errores

**Error al renderizar template**
- Verifica que todas las variables usadas en el template estén definidas
- Las variables deben estar entre llaves: `{variable_name}`
- No uses llaves que no sean variables

## Migración de Prompts Antiguos

Si tenías prompts hardcodeados en el código:

1. Los prompts antiguos están como fallback en el código
2. Una vez inicializados los prompts en BD, estos tienen prioridad
3. Puedes modificar los prompts de BD sin afectar el código
4. El sistema siempre usa primero los prompts de BD si existen
