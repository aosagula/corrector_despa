# Métodos de Extracción de Datos

El sistema soporta dos métodos de extracción de datos de documentos:

## 1. Extracción basada en OCR (Texto)

**Método por defecto**. Utiliza Tesseract OCR para extraer texto de PDFs e imágenes, y luego utiliza un modelo LLM (como Phi-4) para analizar el texto y extraer datos estructurados.

### Ventajas
- Más rápido
- Menor uso de memoria
- Funciona bien con documentos limpios y bien escaneados
- Menor consumo de recursos

### Desventajas
- Depende de la calidad del OCR
- Puede fallar con documentos de baja calidad
- No entiende el layout visual del documento

### Configuración

```env
EXTRACTION_METHOD=ocr
OLLAMA_MODEL=phi4-mini
```

## 2. Extracción basada en Visión (Imagen)

Utiliza modelos multimodales de visión (como Qwen2.5-VL) que procesan directamente las imágenes del documento sin necesidad de OCR intermedio.

### Ventajas
- Entiende el layout visual y estructura del documento
- Mejor con documentos complejos, tablas, gráficos
- No depende de la calidad del OCR
- Puede interpretar contexto visual (colores, posiciones, formato)

### Desventajas
- Más lento
- Mayor uso de memoria y GPU
- Requiere modelos multimodales específicos

### Configuración

```env
EXTRACTION_METHOD=vision
VISION_MODEL=qwen2.5-vl:3b
```

## Cómo Cambiar el Método de Extracción

### Paso 1: Actualizar el archivo `.env`

Edita el archivo `.env` en la raíz del proyecto:

**Para usar OCR:**
```env
EXTRACTION_METHOD=ocr
```

**Para usar Visión:**
```env
EXTRACTION_METHOD=vision
VISION_MODEL=qwen2.5-vl:3b
```

### Paso 2: Descargar el modelo de visión (si usas vision)

Si cambias a método `vision`, necesitas descargar el modelo primero:

```bash
docker-compose exec ollama ollama pull qwen2.5-vl:3b
```

O cualquier otro modelo multimodal compatible:
- `llava:7b`
- `llava:13b`
- `qwen2-vl:7b`
- `qwen2.5-vl:3b`
- Etc.

### Paso 3: Reiniciar el backend

```bash
docker-compose restart backend
```

## Flujo de Procesamiento

### Método OCR

1. Usuario sube documento (PDF/imagen)
2. Sistema extrae texto con Tesseract OCR
3. Phi-4 clasifica el tipo de documento basándose en el texto
4. Phi-4 extrae datos estructurados del texto
5. Datos se guardan en la base de datos

### Método Vision

1. Usuario sube documento (PDF/imagen)
2. Sistema extrae texto con OCR (solo para guardar en `text_content`)
3. Phi-4 clasifica el tipo de documento basándose en el texto
4. **PDF se convierte a imágenes (una por página)**
5. **Qwen2.5-VL analiza las imágenes directamente**
6. **Modelo de visión extrae datos estructurados de las imágenes**
7. Datos se guardan en la base de datos

## Nota Importante

⚠️ **La clasificación siempre usa OCR/texto**, independientemente del método de extracción configurado. Solo la **extracción de datos estructurados** varía según el método.

Esto se debe a que:
- La clasificación es rápida y no requiere análisis visual profundo
- Permite usar modelos más pequeños para clasificación (Phi-4)
- Reserva el modelo de visión pesado solo para extracción detallada

## Modelos Recomendados

### Para OCR
- `phi4-mini` - Rápido, bueno para uso general
- `phi3` - Alternativa más pequeña
- `llama3.1` - Para mayor precisión

### Para Vision
- `qwen2.5-vl:3b` - Balanceado (recomendado para GPU 8GB+)
- `llava:7b` - Alternativa popular
- `llava:13b` - Mayor precisión (requiere más GPU)

## Requisitos del Sistema

### OCR
- CPU: 2+ cores
- RAM: 4GB+
- GPU: Opcional (acelera inferencia del LLM)

### Vision
- CPU: 4+ cores
- RAM: 8GB+
- GPU: **Recomendado** 8GB+ VRAM
- Espacio: 5-10GB adicional para modelos de visión

## Troubleshooting

### Error: "pdf2image no instalado"
```bash
docker-compose exec backend pip install pdf2image
```

### Error: "poppler no encontrado"
Asegúrate de que el Dockerfile incluya poppler-utils:
```dockerfile
RUN apt-get update && apt-get install -y \\
    poppler-utils \\
    tesseract-ocr \\
    tesseract-ocr-spa
```

### Modelo de visión muy lento
- Reduce el DPI de conversión de PDF (por defecto 200)
- Usa un modelo más pequeño (qwen2.5-vl:3b en lugar de :7b)
- Asegúrate de tener GPU habilitada en Docker

### Errores de memoria con Vision
- Reduce el tamaño del batch (procesar páginas de a una)
- Usa un modelo más pequeño
- Aumenta la RAM/VRAM disponible para Docker
