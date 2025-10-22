#!/bin/bash

# Script de configuración inicial para Corrector de Documentos

echo "╔════════════════════════════════════════════════════════╗"
echo "║   Corrector de Documentos - Setup Inicial             ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Verificar que Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado. Por favor, instala Docker primero."
    exit 1
fi

# Verificar que Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado. Por favor, instala Docker Compose primero."
    exit 1
fi

echo "✅ Docker y Docker Compose encontrados"
echo ""

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env desde .env.example..."
    cp .env.example .env
    echo "✅ Archivo .env creado. Puedes editarlo según tus necesidades."
else
    echo "ℹ️  Archivo .env ya existe"
fi

echo ""

# Crear directorio de uploads
echo "📁 Creando directorio de uploads..."
mkdir -p backend/uploads
touch backend/uploads/.gitkeep

echo ""
echo "🚀 Iniciando servicios con Docker Compose..."
docker-compose up -d

echo ""
echo "⏳ Esperando a que los servicios estén listos..."
sleep 10

# Verificar que Ollama esté corriendo
echo ""
echo "🤖 Verificando Ollama..."
if docker ps | grep -q corrector_ollama; then
    echo "✅ Ollama está corriendo"

    echo ""
    echo "📥 Descargando modelo Phi-4..."
    echo "⚠️  ADVERTENCIA: Esto puede tomar varios minutos (el modelo pesa varios GB)"
    docker exec -it corrector_ollama ollama pull phi4

    if [ $? -eq 0 ]; then
        echo "✅ Modelo Phi-4 descargado exitosamente"
    else
        echo "⚠️  Error descargando Phi-4. Puedes intentar manualmente con:"
        echo "   docker exec -it corrector_ollama ollama pull phi4"
    fi
else
    echo "❌ Ollama no está corriendo"
fi

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║   ¡Configuración completada!                          ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Accede a la aplicación en:"
echo "   Frontend: http://localhost"
echo "   API Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "📋 Próximos pasos:"
echo "   1. Abre http://localhost en tu navegador"
echo "   2. Ve a 'Configurar Atributos'"
echo "   3. Haz clic en 'Cargar Atributos por Defecto'"
echo "   4. ¡Empieza a subir documentos!"
echo ""
echo "🛠️  Comandos útiles:"
echo "   Ver logs:      docker-compose logs -f"
echo "   Detener:       docker-compose down"
echo "   Reiniciar:     docker-compose restart"
echo ""
