// Archivo de ejemplo de configuración del frontend
// Copia este archivo como config.js y ajusta según tu entorno

// API Configuration
const API_CONFIG = {
    // URL base del backend API
    // En desarrollo: apunta a localhost:8000
    // En producción/Docker: usa el proxy de nginx
    baseURL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8000/api/v1'  // Desarrollo local
        : `${window.location.protocol}//${window.location.host}/api/v1`,  // Producción

    // Timeout para requests (especialmente uploads de archivos)
    timeout: 60000  // 60 segundos
};

// Constante global para compatibilidad con código legacy
const API_BASE_URL = API_CONFIG.baseURL;

// Función helper para construir URLs completas de API
function getApiUrl(endpoint) {
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${API_CONFIG.baseURL}${normalizedEndpoint}`;
}

// NOTAS DE CONFIGURACIÓN:
// ========================
//
// Para desarrollo local:
// - El frontend se conecta directamente a http://localhost:8000
// - Requiere que el backend esté corriendo en el puerto 8000
// - CORS debe estar habilitado en el backend
//
// Para producción/Docker:
// - El frontend usa rutas relativas (/api/v1)
// - nginx hace proxy a http://backend:8000
// - No hay problemas de CORS porque todo está en el mismo dominio
//
// Para personalizar la URL del backend:
// - Opción 1: Modificar directamente este archivo
// - Opción 2: Usar variables globales en index.html antes de cargar este script:
//   <script>
//     window.API_BACKEND_URL = 'https://mi-api.ejemplo.com/api/v1';
//   </script>
