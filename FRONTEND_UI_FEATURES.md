# Interfaz de Usuario - Características

## Gestión Visual de Prompts

La interfaz web ahora incluye una sección completa para gestionar prompts de forma visual e intuitiva.

## Acceso

1. Iniciar la aplicación:
```bash
cd backend
uvicorn app.main:app --reload
```

2. Abrir en el navegador: `http://localhost:8000`

3. En el menú lateral, hacer clic en "Gestión de Prompts"

## Características Principales

### 📊 Vista de Lista Organizada

- **Agrupación inteligente**: Los prompts se organizan automáticamente
  - Prompts de clasificación en su propia sección
  - Prompts de extracción agrupados por tipo de documento

- **Información clara**: Cada prompt muestra
  - Nombre del prompt
  - Descripción breve
  - Estado (activo/inactivo) con badge de color
  - Fecha de creación
  - Acciones rápidas

### 🔍 Filtros Avanzados

- **Por tipo**: Filtrar entre clasificación, extracción o todos
- **Por estado**: Checkbox para mostrar solo prompts activos
- **Actualización instantánea**: Los filtros se aplican inmediatamente

### ✏️ Editor de Prompts

Modal completo para crear/editar prompts con:

**Campos del formulario:**
- Nombre del prompt (obligatorio)
- Tipo: Clasificación o Extracción (obligatorio)
- Tipo de documento (obligatorio solo para extracción)
- Template del prompt con editor de texto grande (obligatorio)
- Descripción del prompt (opcional)
- Checkbox de activación

**Validaciones automáticas:**
- Nombres únicos
- Tipo de documento requerido para extracción
- Template no puede estar vacío
- Extracción de variables automática del template

**Variables soportadas:**
- `{text_content}`: Contenido del documento
- `{document_type}`: Tipo de documento

### 👁️ Vista de Detalle

Modal de solo lectura que muestra:
- Toda la información del prompt
- Template formateado y legible
- Variables con sus descripciones
- Fechas de creación y última actualización
- Badges de estado y tipo

### 🎯 Acciones Rápidas

Desde la lista, cada prompt tiene botones para:

1. **Ver** (👁️): Abre modal de detalle
2. **Editar** (✏️): Abre modal de edición
3. **Activar/Desactivar** (🔄): Toggle de estado instantáneo
4. **Eliminar** (🗑️): Elimina el prompt (con confirmación)

### ⚡ Inicialización Rápida

Botón "Inicializar Defaults" que:
- Carga 7 prompts predefinidos (1 clasificación + 6 extracción)
- Solo funciona si la BD está vacía
- Confirma antes de ejecutar
- Muestra feedback de éxito/error

## Diseño y UX

### 🎨 Interfaz Moderna

- **Bootstrap 5**: Framework de UI moderno y responsive
- **Bootstrap Icons**: Iconografía consistente
- **Temas de color**: Código de colores intuitivo
  - Verde: Activo, Extracción
  - Gris: Inactivo
  - Azul: Clasificación, Acciones primarias
  - Rojo: Eliminar, Errores

### 📱 Responsive Design

- Funciona en desktop, tablet y móvil
- Tablas responsivas con scroll horizontal
- Modales adaptables al tamaño de pantalla
- Botones agrupados para espacios pequeños

### ⚙️ Experiencia de Usuario

**Feedback visual:**
- Spinners durante operaciones
- Alertas de éxito/error con auto-dismiss
- Estados hover en elementos interactivos
- Animaciones suaves

**Confirmaciones:**
- Eliminar prompt requiere confirmación
- Inicializar defaults requiere confirmación

**Validación en tiempo real:**
- Campos requeridos marcados claramente
- Mensajes de ayuda contextuales
- Validación antes de enviar

## Flujo de Trabajo Típico

### Primera Vez

```
1. Abrir "Gestión de Prompts"
2. Ver mensaje "No hay prompts configurados"
3. Clic en "Inicializar Defaults"
4. Confirmar
5. Ver 7 prompts cargados y organizados
```

### Crear Prompt Personalizado

```
1. Clic en "Nuevo Prompt"
2. Llenar formulario:
   - Nombre: extraction_factura_v2
   - Tipo: Extracción
   - Documento: Factura
   - Template: [tu prompt]
   - Descripción: Versión mejorada
   - Activo: No (para probar primero)
3. Guardar
4. Ver nuevo prompt en la lista (inactivo)
```

### Modificar Prompt Existente

```
1. Localizar prompt en la lista
2. Clic en botón de editar (✏️)
3. Modificar campos necesarios
4. Guardar
5. Ver cambios reflejados inmediatamente
```

### Cambiar de Prompt Activo

```
1. Filtrar por tipo si es necesario
2. Localizar el prompt nuevo que quieres activar
3. Clic en botón toggle (🔄)
4. Confirmar que el badge cambió a "Activo"
5. El anterior del mismo tipo se desactiva automáticamente
```

## Código de Colores

### Badges de Estado
- 🟢 **Verde** (`Activo`): Este prompt se está usando
- ⚫ **Gris** (`Inactivo`): Prompt disponible pero no en uso

### Badges de Tipo
- 🔵 **Azul** (`Clasificación`): Determina tipo de documento
- 🟢 **Verde** (`Extracción`): Extrae datos del documento

### Botones de Acción
- 🔵 **Azul** (Info/Ver): Acción de solo lectura
- 🔵 **Azul** (Primario/Editar): Acción principal
- 🟡 **Amarillo** (Warning/Desactivar): Acción reversible
- 🟢 **Verde** (Success/Activar): Acción positiva
- 🔴 **Rojo** (Danger/Eliminar): Acción destructiva

## Arquitectura Frontend

### Archivos del Sistema

```
frontend/
├── index.html              # HTML principal (modificado)
├── js/
│   ├── config.js          # Configuración de API
│   ├── api.js             # Funciones API (extendido)
│   ├── prompts.js         # Módulo de gestión de prompts (NUEVO)
│   └── app.js             # Lógica principal de la app
└── css/
    └── style.css          # Estilos (extendido)
```

### Clase Principal: PromptsManager

**Responsabilidades:**
- Gestión del estado de la UI
- Carga y renderizado de prompts
- Manejo de modals
- Eventos de usuario
- Comunicación con API
- Feedback visual

**Métodos principales:**
```javascript
- loadPrompts()           // Carga lista de prompts
- renderPromptsList()     // Renderiza la lista
- openCreateModal()       // Abre modal para crear
- editPrompt(id)          // Abre modal para editar
- viewPrompt(id)          // Muestra detalle
- savePrompt()            // Guarda cambios
- deletePrompt(id)        // Elimina prompt
- toggleActive(id, state) // Cambia estado
- initializeDefaults()    // Carga defaults
```

### API Frontend

Nuevas funciones en `api.js`:

```javascript
DocumentAPI.listPrompts(type, activeOnly)
DocumentAPI.getPrompt(id)
DocumentAPI.getPromptByName(name)
DocumentAPI.getActiveClassificationPrompt()
DocumentAPI.getActiveExtractionPrompt(docType)
DocumentAPI.createPrompt(data)
DocumentAPI.updatePrompt(id, data)
DocumentAPI.deletePrompt(id)
DocumentAPI.initializeDefaultPrompts()
```

## Integración con Backend

La UI se comunica con estos endpoints:

```
GET    /api/v1/prompts/                         → Lista prompts
GET    /api/v1/prompts/{id}                     → Obtiene prompt
GET    /api/v1/prompts/name/{name}              → Obtiene por nombre
GET    /api/v1/prompts/classification/active    → Clasificación activa
GET    /api/v1/prompts/extraction/{type}/active → Extracción activa
POST   /api/v1/prompts/                         → Crea prompt
PUT    /api/v1/prompts/{id}                     → Actualiza prompt
DELETE /api/v1/prompts/{id}                     → Elimina prompt
POST   /api/v1/prompts/initialize-defaults      → Init defaults
```

## Casos de Uso Avanzados

### Versionado de Prompts

La UI facilita mantener múltiples versiones:

1. **Ver todas las versiones**: Sin filtros
2. **Activar versión específica**: Toggle en la versión deseada
3. **Comparar versiones**: Ver detalles de cada una
4. **Rollback**: Activar versión anterior

### Testing A/B

Para comparar dos prompts:

1. Crear dos versiones: `prompt_a` y `prompt_b`
2. Probar con `prompt_a` activo, procesar documentos
3. Desactivar `prompt_a`, activar `prompt_b`
4. Procesar mismos documentos
5. Comparar resultados
6. Mantener el mejor

### Gestión por Equipo

Múltiples usuarios pueden:

1. Ver todos los prompts disponibles
2. Crear nuevos prompts (con nombres únicos)
3. Solo un prompt activo por tipo/documento
4. Historial visible en fechas de creación/modificación

## Métricas y Monitoreo

### Información Visible en UI

- **Cantidad de prompts**: Total en la lista
- **Estado de activación**: Qué prompts están en uso
- **Última modificación**: Fechas en cada prompt
- **Cobertura**: Qué tipos de documento tienen prompts

### Información No Visible (Futuras Mejoras)

- Uso de cada prompt (cuántos documentos procesados)
- Tasa de éxito/error por prompt
- Tiempo promedio de procesamiento
- Comparación de performance entre versiones

## Seguridad

### Validaciones

- **Client-side**: Formularios validados antes de enviar
- **Server-side**: API valida todos los datos
- **Nombres únicos**: No permite duplicados
- **Confirmaciones**: Acciones destructivas requieren confirmación

### Limitaciones Actuales

- No hay autenticación de usuarios (futuro)
- No hay control de permisos por rol (futuro)
- No hay audit log de cambios (futuro)

## Performance

### Optimizaciones

- **Carga lazy**: Prompts solo se cargan al abrir el tab
- **Filtrado client-side**: Filtros instantáneos
- **Renderizado eficiente**: Solo actualiza lo necesario
- **Spinners**: Feedback visual durante operaciones

### Límites

- Maneja bien hasta ~100 prompts
- Para más, considerar paginación (futuro)

## Troubleshooting de UI

### Problema: Lista no carga

**Síntomas**: "Cargando prompts..." sin cambiar

**Causas posibles:**
- Backend no está corriendo
- URL de API incorrecta
- Problemas de CORS

**Solución:**
1. Verificar backend: `http://localhost:8000/health`
2. Abrir consola del navegador (F12)
3. Ver errores de red
4. Verificar `config.js` tiene URL correcta

### Problema: No puedo guardar

**Síntomas**: Botón "Guardar" no responde o error

**Causas posibles:**
- Validación de formulario fallando
- Nombre duplicado
- Campos requeridos vacíos

**Solución:**
1. Verificar todos los campos requeridos
2. Usar nombre único
3. Ver consola del navegador por errores
4. Verificar mensaje de error en la UI

### Problema: Cambios no se reflejan

**Síntomas**: Guardé pero no veo cambios

**Solución:**
1. Refrescar la página
2. Verificar que el prompt está activo
3. Ver que es el único activo de su tipo
4. Revisar logs del backend

## Mejoras Futuras

### Próxima Versión (v1.1)

- [ ] Búsqueda por texto en prompts
- [ ] Clonación de prompts con un clic
- [ ] Export/import de prompts (JSON)
- [ ] Comparación visual lado a lado
- [ ] Preview de variables en el template

### Versión 2.0

- [ ] Editor de código con syntax highlighting
- [ ] Autocompletado de variables
- [ ] Templates predefinidos
- [ ] Biblioteca compartida de prompts
- [ ] Historial de cambios por prompt
- [ ] Métricas de uso en tiempo real
- [ ] Testing A/B integrado
- [ ] Autenticación y roles

## Feedback y Contribuciones

Para reportar bugs o sugerir mejoras:

1. Documentar el problema/idea claramente
2. Incluir capturas de pantalla si aplica
3. Abrir issue en el repositorio
4. Etiquetar como `ui` o `prompts`

## Documentación Relacionada

- **PROMPT_MANAGEMENT.md**: Documentación de la API
- **FRONTEND_PROMPTS_GUIDE.md**: Guía de usuario detallada
- **CAMBIOS_PROMPT_MANAGEMENT.md**: Resumen de implementación

---

**Versión**: 1.0.0
**Fecha**: 2024-10-23
**Autor**: Sistema de Gestión de Prompts
