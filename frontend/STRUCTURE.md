# Estructura del Frontend

El frontend ha sido reorganizado en páginas separadas con navegación mediante menú.

## Estructura de Archivos

```
frontend/
├── index.html                          # Dashboard principal
├── pages/                              # Páginas individuales
│   ├── upload-commercial.html         # Subir documentos comerciales
│   ├── upload-provisional.html        # Subir documentos provisorios
│   ├── compare.html                   # Comparar documentos
│   ├── prompts.html                   # Gestión de prompts
│   ├── page-types.html                # Tipos de páginas
│   ├── page-detection.html            # Detectar páginas
│   ├── attribute-extraction.html      # Configurar atributos
│   └── history.html                   # Historial de comparaciones
├── js/
│   ├── modules/                       # Módulos JavaScript por página
│   │   ├── components.js              # Navbar y Sidebar compartidos
│   │   ├── dashboard.js               # Lógica del dashboard
│   │   ├── upload-commercial.js       # Lógica de documentos comerciales
│   │   ├── upload-provisional.js      # Lógica de documentos provisorios
│   │   ├── compare.js                 # Lógica de comparación
│   │   └── history.js                 # Lógica de historial
│   ├── config.js                      # Configuración
│   ├── api.js                         # Funciones de API
│   ├── app.js                         # (legacy - mantener por compatibilidad)
│   ├── prompts.js                     # Gestión de prompts
│   ├── page-types.js                  # Tipos de páginas
│   ├── detection-rules.js             # Reglas de detección
│   ├── page-detection.js              # Detección de páginas
│   └── attribute-extraction-new.js    # Configuración de atributos
├── css/
│   └── style.css                      # Estilos
├── components/                         # (carpeta reservada para futuros componentes)
└── images/                            # Imágenes y recursos
```

## Navegación

- **Navbar**: Barra superior con logo y enlace al inicio
- **Sidebar**: Menú lateral con enlaces a todas las páginas:
  - Dashboard (inicio)
  - Documentos Comerciales
  - Documento Provisorio
  - Comparar
  - Gestión de Prompts
  - Tipos de Páginas
  - Detectar Páginas
  - Configurar Atributos
  - Historial

## Componentes Compartidos

### components.js
- `renderNavbar()`: Renderiza la barra de navegación superior
- `renderSidebar(activePage)`: Renderiza el menú lateral con página activa marcada

Estos componentes se cargan automáticamente en todas las páginas.

## Páginas

### 1. Dashboard (index.html)
- Estadísticas rápidas (documentos, comparaciones, prompts)
- Acciones rápidas (botones a páginas principales)
- Actividad reciente

### 2. Documentos Comerciales
- Formulario para subir documentos comerciales
- Lista de documentos subidos
- Ver/eliminar documentos

### 3. Documento Provisorio
- Formulario para subir documentos provisorios
- Lista de documentos provisorios
- Ver/eliminar documentos

### 4. Comparar
- Selección de documento comercial y provisorio
- Botón para comparar
- Botón para comparar con todos
- Resultados de comparaciones

### 5. Gestión de Prompts
- Filtros por tipo y estado
- Lista de prompts configurados
- Crear/editar prompts
- Inicializar prompts por defecto

### 6. Tipos de Páginas
- Lista de tipos de páginas
- Crear/editar tipos de páginas
- Configurar reglas de detección

### 7. Detectar Páginas
- Visor de documentos
- Detección automática de tipos de página
- Clasificación manual

### 8. Configurar Atributos
- Configuración de atributos de extracción
- Definir qué datos extraer de cada tipo de documento

### 9. Historial
- Lista de todas las comparaciones realizadas
- Ver detalles de cada comparación
- Estado (coincide/no coincide)

## Migración desde la versión anterior

La versión anterior usaba Bootstrap tabs en una sola página. La nueva estructura:

✅ **Ventajas:**
- Mejor organización del código
- URLs específicas para cada sección
- Más fácil de mantener y escalar
- Menor carga inicial (cada página carga solo su JS necesario)
- Mejor para SEO (si fuera público)
- Navegación más clara

⚠️ **Notas de compatibilidad:**
- Los archivos JS legacy (`app.js`, `prompts.js`, etc.) se mantienen para las páginas que los necesiten
- Las funciones comunes (toast, modales) se duplican en cada módulo para independencia

## Próximos pasos sugeridos

Si quieres mejorar aún más la arquitectura:

1. **Crear archivo de utilidades compartidas** (`js/utils.js`) para funciones como `showToast()`
2. **Componentes HTML reutilizables** (modales, cards) en `components/`
3. **Sistema de routing** con JavaScript (SPA) si prefieres evitar recargas de página
4. **Migración a React/Next.js** cuando el proyecto crezca significativamente
