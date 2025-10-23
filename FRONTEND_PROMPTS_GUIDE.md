# Guía de Usuario - Interfaz de Gestión de Prompts

Esta guía explica cómo usar la interfaz web para gestionar los prompts de clasificación y extracción de documentos.

## Acceso a la Interfaz

1. **Iniciar el Backend**:
```bash
cd backend
uvicorn app.main:app --reload
```

2. **Abrir el Frontend**:
   - Navegador web: `http://localhost:8000` (si está servido por FastAPI)
   - O abrir directamente `frontend/index.html` en el navegador

3. **Navegar a Gestión de Prompts**:
   - En el menú lateral izquierdo, hacer clic en "Gestión de Prompts"

## Vista Principal

La vista principal muestra:

### Filtros y Acciones
- **Filtrar por Tipo**: Selecciona entre todos, clasificación o extracción
- **Solo activos**: Checkbox para mostrar únicamente prompts activos
- **Nuevo Prompt**: Botón para crear un nuevo prompt
- **Inicializar Defaults**: Botón para cargar prompts por defecto (primera vez)

### Lista de Prompts

Los prompts se organizan en dos secciones:

#### Prompts de Clasificación
- Tabla con todos los prompts de clasificación
- Muestra: nombre, descripción, estado (activo/inactivo), fecha de creación
- Acciones disponibles en cada fila

#### Prompts de Extracción
- Agrupados por tipo de documento (factura, orden de compra, etc.)
- Cada grupo muestra sus prompts en una tabla
- Mismas columnas y acciones que clasificación

## Funcionalidades

### 1. Inicializar Prompts por Defecto

**Primera vez usando el sistema:**

1. Hacer clic en el botón "Inicializar Defaults"
2. Confirmar la acción
3. El sistema carga 7 prompts:
   - 1 prompt de clasificación
   - 6 prompts de extracción (uno por cada tipo de documento)

**Nota**: Esta acción solo funciona si la base de datos está vacía.

### 2. Ver Detalle de un Prompt

1. En la lista de prompts, hacer clic en el ícono de ojo (👁️) en la fila del prompt
2. Se abre un modal con información completa:
   - Nombre y estado
   - Tipo de prompt
   - Tipo de documento (si aplica)
   - Descripción
   - Template completo del prompt
   - Variables disponibles
   - Fechas de creación y actualización

### 3. Crear un Nuevo Prompt

1. Hacer clic en el botón "Nuevo Prompt"
2. En el formulario completar:

#### Campos Requeridos:
- **Nombre del Prompt**: Identificador único (ej: `extraction_factura_v2`)
- **Tipo**: Seleccionar "Clasificación" o "Extracción"
- **Template del Prompt**: El texto del prompt con variables

#### Campos Opcionales:
- **Tipo de Documento**: Requerido solo para prompts de extracción
- **Descripción**: Descripción del propósito del prompt
- **Prompt activo**: Checkbox para activar inmediatamente

3. Hacer clic en "Guardar"

#### Variables Disponibles en Templates:

- `{text_content}`: Contenido de texto del documento
- `{document_type}`: Tipo de documento (solo para extracción)

#### Ejemplo de Template de Clasificación:

```
Analiza el siguiente documento y determina su tipo:

{text_content}

Responde en formato JSON:
{"document_type": "tipo", "confidence": 0.95, "reasoning": "explicación"}
```

#### Ejemplo de Template de Extracción:

```
Extrae los siguientes datos del documento tipo "{document_type}":

{text_content}

Campos a extraer:
- numero_factura
- fecha
- monto_total
- proveedor

Responde en formato JSON con los campos encontrados.
```

### 4. Editar un Prompt Existente

1. En la lista, hacer clic en el ícono de lápiz (✏️) en la fila del prompt
2. El formulario se abre pre-llenado con los datos actuales
3. Modificar los campos necesarios
4. Hacer clic en "Guardar"

**Notas**:
- No puedes cambiar el tipo de un prompt existente (clasificación/extracción)
- Si modificas un prompt activo, los cambios se aplican inmediatamente

### 5. Activar/Desactivar un Prompt

**Opción 1: Desde la lista**
1. Hacer clic en el ícono de toggle (🔄) en la fila del prompt
2. El estado cambia automáticamente

**Opción 2: Al editar**
1. Abrir el formulario de edición
2. Marcar/desmarcar el checkbox "Prompt activo"
3. Guardar

**Importante**:
- Solo puede haber un prompt activo por tipo/documento
- Si activas un prompt, los demás del mismo tipo/documento se desactivan automáticamente

### 6. Eliminar un Prompt

1. En la lista, hacer clic en el ícono de basura (🗑️) en la fila del prompt
2. Confirmar la eliminación en el diálogo
3. El prompt se elimina permanentemente

**⚠️ Advertencia**: Esta acción no se puede deshacer.

## Buenas Prácticas

### Versionado de Prompts

En lugar de eliminar prompts antiguos, crea versiones nuevas:

```
extraction_factura_v1  → Inactivo (versión anterior)
extraction_factura_v2  → Activo (versión actual)
extraction_factura_v3  → Inactivo (versión experimental)
```

Ventajas:
- Mantener historial de cambios
- Poder volver a versión anterior fácilmente
- Comparar diferentes versiones

### Pruebas de Prompts

Antes de activar un nuevo prompt:

1. Crear el prompt como **inactivo**
2. Probarlo en un ambiente de desarrollo
3. Validar resultados con documentos reales
4. Solo entonces activarlo en producción

### Descripción Clara

Siempre incluye una descripción que explique:
- Propósito del prompt
- Qué lo diferencia de otros
- Cuándo usarlo
- Autor/fecha si es relevante

Ejemplo:
```
Prompt mejorado para extracción de facturas internacionales.
Incluye soporte para múltiples monedas y formatos de fecha.
Creado por Juan - 2024-10-23
```

### Nombramiento Consistente

Usa una convención de nombres clara:

**Clasificación**:
- `classification_default`
- `classification_v2_multilang`
- `classification_custom_industria`

**Extracción**:
- `extraction_{tipo_documento}_v{version}`
- Ejemplos:
  - `extraction_factura_v1`
  - `extraction_orden_compra_v2`
  - `extraction_contrato_detailed`

## Flujo de Trabajo Recomendado

### Primera Configuración

1. Hacer clic en "Inicializar Defaults"
2. Revisar cada prompt creado (hacer clic en el ícono de ojo)
3. Probar con documentos reales
4. Si es necesario, crear versiones personalizadas

### Modificar un Prompt

1. Ver el prompt actual (ícono de ojo)
2. Crear un nuevo prompt basado en el actual
3. Asignar nuevo nombre con versión incrementada
4. Mantenerlo inactivo inicialmente
5. Probar exhaustivamente
6. Activar cuando esté listo
7. Mantener el anterior inactivo como backup

### Gestión de Múltiples Versiones

**Escenario**: Probar varios prompts para facturas

1. Crear prompts:
   - `extraction_factura_original` (activo)
   - `extraction_factura_detallado` (inactivo)
   - `extraction_factura_simple` (inactivo)

2. Para probar `extraction_factura_detallado`:
   - Desactivar `extraction_factura_original`
   - Activar `extraction_factura_detallado`
   - Procesar documentos de prueba
   - Evaluar resultados

3. Comparar resultados

4. Mantener el mejor como activo

## Filtros Útiles

### Ver Solo Prompts Activos
1. Marcar checkbox "Solo activos"
2. Ver qué prompts están en uso actualmente

### Ver Prompts de Clasificación
1. Filtrar por tipo: "Clasificación"
2. Ver/editar el prompt de clasificación actual

### Ver Prompts de un Tipo de Documento
1. Filtrar por tipo: "Extracción"
2. Buscar en la sección del tipo de documento específico

## Solución de Problemas

### No se muestran prompts

**Problema**: La lista está vacía

**Solución**:
1. Hacer clic en "Inicializar Defaults"
2. Verificar que el backend esté corriendo
3. Revisar la consola del navegador (F12) por errores

### Error al guardar prompt

**Problema**: "Error creating prompt: Ya existe un prompt con ese nombre"

**Solución**:
- Cambiar el nombre del prompt a uno único
- Usar versionado (v1, v2, etc.)

**Problema**: "prompt_type debe ser 'classification' o 'extraction'"

**Solución**:
- Asegurarse de seleccionar un tipo en el formulario

**Problema**: "Los prompts de extracción deben especificar un document_type"

**Solución**:
- Para prompts de extracción, seleccionar un tipo de documento

### Prompt no se aplica

**Problema**: Modificaste un prompt pero no ves cambios

**Solución**:
1. Verificar que el prompt esté marcado como "Activo"
2. Solo hay un prompt activo por tipo/documento
3. Refrescar la página después de modificar

### No puedo eliminar un prompt

**Problema**: Error al eliminar

**Solución**:
- Verificar conexión con el backend
- Revisar permisos
- Ver logs del backend para más detalles

## Atajos de Teclado

Cuando el modal está abierto:
- **Esc**: Cerrar modal
- **Ctrl/Cmd + Enter**: Guardar (cuando está en el formulario)

## Tips de Productividad

### Duplicar un Prompt

Para crear una copia de un prompt:
1. Ver el prompt original (ícono de ojo)
2. Copiar el template del prompt
3. Crear nuevo prompt (botón "Nuevo Prompt")
4. Pegar el template
5. Modificar nombre y otros campos
6. Guardar

### Comparar Prompts

Para comparar dos prompts:
1. Abrir primer prompt en el modal de detalle
2. Copiar su template a un editor de texto
3. Abrir segundo prompt
4. Comparar manualmente los templates

### Export/Backup

Actualmente la UI no tiene función de export, pero puedes:
1. Ver el prompt en el modal de detalle
2. Copiar manualmente el template
3. Guardarlo en un archivo de texto

## Mejores Prácticas de UI

### Navegación Eficiente

1. Usa los filtros para reducir la lista
2. Los prompts están agrupados lógicamente
3. La búsqueda es instantánea al cambiar filtros

### Edición Rápida

1. Para cambios menores, usa el botón de editar directamente
2. Para cambios mayores, crea un nuevo prompt

### Verificación Visual

Los badges de color te ayudan a identificar:
- **Verde**: Activo
- **Gris**: Inactivo
- **Azul**: Clasificación
- **Verde claro**: Extracción

## Próximas Características

Posibles mejoras futuras:
- Export/import de prompts
- Comparación visual de dos prompts
- Historial de cambios por prompt
- Clonación de prompts con un clic
- Búsqueda por texto en templates
- Previsualización de resultados
- Estadísticas de uso por prompt

## Feedback y Soporte

Si encuentras problemas o tienes sugerencias:
1. Revisar esta guía primero
2. Verificar logs del backend
3. Abrir un issue en el repositorio
4. Contactar al equipo de desarrollo

---

**Última actualización**: 2024-10-23
**Versión de la UI**: 1.0.0
