// Cache busting version - updates automatically
const ASSETS_VERSION = Date.now();

// API Configuration
const API_CONFIG = {
    // Detección automática del backend según el entorno
    // Permite override con window.API_BACKEND_URL si está definido
    // - Desarrollo local: http://localhost:8000/api/v1
    // - Producción/Docker: /api/v1 (proxy nginx)
    // - Custom: usar window.API_BACKEND_URL en index.html
    baseURL: window.API_BACKEND_URL || (
        window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
            ? 'http://localhost:8000/api/v1'
            : `${window.location.protocol}//${window.location.host}/api/v1`
    ),
    timeout: 60000 // 60 seconds for file uploads
};

// Exportar como constante global para compatibilidad
const API_BASE_URL = API_CONFIG.baseURL;

// Helper function to get full API URL
function getApiUrl(endpoint) {
    // Asegurar que el endpoint empiece con /
    const normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    return `${API_CONFIG.baseURL}${normalizedEndpoint}`;
}

// Log de configuración en desarrollo
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('[Config] API Backend URL:', API_CONFIG.baseURL);
}
