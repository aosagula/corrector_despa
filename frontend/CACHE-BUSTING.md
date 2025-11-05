# Cache Busting - Guía para Evitar Problemas de Caché

## Problema
Los navegadores cachean archivos JavaScript y CSS, lo que puede causar que los usuarios vean versiones antiguas después de actualizaciones.

## Soluciones Implementadas

### 1. Meta Tags HTTP en HTML (✓ Implementado)
Todos los archivos HTML principales incluyen:
```html
<!-- Cache Control -->
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

**Archivos actualizados:**
- ✓ `index.html`
- ✓ `pages/extract-attributes.html`
- ⚠️  Otros archivos en `pages/` - pendiente

### 2. Variable de Versión en config.js (✓ Implementado)
El archivo `js/config.js` incluye:
```javascript
const ASSETS_VERSION = Date.now();
```

Esta variable se puede usar para versionar archivos dinámicamente.

### 3. Configuración del Servidor Web (Recomendado)

Si usas **Nginx**, agrega al archivo de configuración:
```nginx
location ~* \.(js|css)$ {
    add_header Cache-Control "no-cache, no-store, must-revalidate";
    add_header Pragma "no-cache";
    add_header Expires "0";
}
```

Si usas **Apache**, agrega al `.htaccess`:
```apache
<FilesMatch "\.(js|css)$">
    Header set Cache-Control "no-cache, no-store, must-revalidate"
    Header set Pragma "no-cache"
    Header set Expires "0"
</FilesMatch>
```

## Soluciones Manuales para Desarrollo

### Durante el Desarrollo

**Opción 1: Hard Refresh**
- **Chrome/Edge/Firefox**: `Ctrl + F5` o `Ctrl + Shift + R`
- **Mac**: `Cmd + Shift + R`

**Opción 2: DevTools**
- Abre DevTools (`F12`)
- Ve a Network tab
- Marca "Disable cache"
- Mantén DevTools abierto mientras desarrollas

**Opción 3: Borrar Caché del Navegador**
- Chrome: `Ctrl + Shift + Delete` → Selecciona "Cached images and files"

## Mejores Prácticas

1. **Siempre hacer Hard Refresh** después de actualizar archivos JS/CSS
2. **Verificar en Network Tab** que los archivos se están cargando (no "from cache")
3. **Usar modo incógnito** para probar cambios sin caché
4. **Versionar archivos** en producción usando query strings o hash en nombres

## Para Producción (Futuro)

Considerar implementar:
- Build process que agregue hash a nombres de archivos
- CDN con invalidación de caché
- Service Workers para control preciso de caché
