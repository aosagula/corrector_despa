# Configuración del Frontend

## Variables de Configuración

### URL del Backend API

El frontend detecta automáticamente la URL del backend según el entorno:

#### 1. **Desarrollo Local**
- **Condición**: `hostname === 'localhost'` o `hostname === '127.0.0.1'`
- **URL Backend**: `http://localhost:8000/api/v1`
- **Uso**: Cuando abres el HTML directamente o con un servidor local

#### 2. **Producción/Docker**
- **Condición**: Cualquier otro hostname
- **URL Backend**: `/api/v1` (ruta relativa)
- **Uso**: En Docker, nginx hace proxy al backend en `http://backend:8000`

#### 3. **Configuración Personalizada**
Si necesitas una URL personalizada, puedes definirla en `index.html` antes de cargar `config.js`:

```html
<script>
    // Definir URL personalizada del backend
    window.API_BACKEND_URL = 'https://mi-api.ejemplo.com/api/v1';
</script>
<script src="js/config.js"></script>
```

## Archivos de Configuración

### `js/config.js`
Archivo principal de configuración que se carga en el frontend.

**Contenido:**
- `API_CONFIG.baseURL`: URL base del backend
- `API_CONFIG.timeout`: Timeout para requests (60s)
- `API_BASE_URL`: Constante global (legacy)
- `getApiUrl(endpoint)`: Helper para construir URLs completas

### `config.example.js`
Archivo de ejemplo con documentación detallada.

## Cómo Funciona

### En Desarrollo Local

```javascript
// El navegador está en localhost
API_CONFIG.baseURL = 'http://localhost:8000/api/v1'

// Llamada de ejemplo
fetch(getApiUrl('/documents/commercial'))
// → GET http://localhost:8000/api/v1/documents/commercial
```

### En Docker/Producción

```javascript
// El navegador está en cualquier dominio
API_CONFIG.baseURL = '/api/v1'

// Llamada de ejemplo
fetch(getApiUrl('/documents/commercial'))
// → GET /api/v1/documents/commercial
// nginx hace proxy a → http://backend:8000/api/v1/documents/commercial
```

## Configuración de nginx

El archivo `nginx.conf` está configurado para hacer proxy de `/api/*` al backend:

```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
    # ... headers y timeouts
}
```

## Variables de Entorno (Backend)

El backend usa variables de entorno desde `.env` o docker-compose:

```env
API_V1_STR=/api/v1
OLLAMA_HOST=http://ollama:11434
DB_HOST=db
# ... etc
```

## Debugging

Para ver la URL del backend que se está usando:

1. Abre la consola del navegador (F12)
2. En desarrollo local verás: `[Config] API Backend URL: http://localhost:8000/api/v1`

## Cambiar la URL del Backend

### Opción 1: Modificar config.js directamente
```javascript
baseURL: 'https://mi-backend.com/api/v1'
```

### Opción 2: Variable global en index.html
```html
<script>
    window.API_BACKEND_URL = 'https://mi-backend.com/api/v1';
</script>
```

### Opción 3: Configuración por entorno en nginx
Puedes usar variables de entorno en nginx y generar el config.js dinámicamente.
