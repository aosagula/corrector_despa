// Cache busting version - automatically updates
// This file is loaded first and provides version info for all other assets
const APP_VERSION = Date.now(); // Timestamp-based version

// Function to add version to URLs
function versionUrl(url) {
    const separator = url.includes('?') ? '&' : '?';
    return `${url}${separator}v=${APP_VERSION}`;
}

// Make it globally available
window.APP_VERSION = APP_VERSION;
window.versionUrl = versionUrl;
