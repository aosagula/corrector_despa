#!/bin/bash
# Script para agregar meta tags de cache control a todos los archivos HTML

CACHE_META='    <!-- Cache Control -->
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
'

# Función para procesar un archivo
process_file() {
    local file="$1"

    # Verificar si ya tiene el cache control
    if grep -q "Cache-Control" "$file"; then
        echo "✓ $file ya tiene cache control"
        return
    fi

    # Buscar la línea del title y agregar después
    if grep -q "<title>" "$file"; then
        # Crear archivo temporal
        awk -v meta="$CACHE_META" '
            /<title>/ {
                print
                getline
                print
                print meta
                next
            }
            {print}
        ' "$file" > "$file.tmp"

        mv "$file.tmp" "$file"
        echo "✓ Actualizado: $file"
    else
        echo "✗ No se encontró <title> en: $file"
    fi
}

# Procesar todos los archivos HTML en pages/
echo "Procesando archivos en pages/..."
for file in pages/*.html; do
    if [ -f "$file" ]; then
        process_file "$file"
    fi
done

echo ""
echo "Proceso completado!"
