// API Configuration
const API_CONFIG = {
    baseURL: window.location.hostname === 'localhost'
        ? 'http://localhost:8000/api/v1'
        : '/api/v1',
    timeout: 60000 // 60 seconds for file uploads
};

// Helper function to get full API URL
function getApiUrl(endpoint) {
    return `${API_CONFIG.baseURL}${endpoint}`;
}
