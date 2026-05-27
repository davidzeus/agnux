#!/bin/bash
# ================================================
# AGNUX Setup Script
# Automatiza la instalación inicial de AGNUX
# ================================================

set -e  # Salir si hay error

echo "🚀 ============================================"
echo "   AGNUX Installation & Setup Script"
echo "============================================"

# Detectar SO
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ Este script solo funciona en Linux"
    exit 1
fi

# 1. Verificar Python
echo ""
echo "📦 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 no está instalado"
    echo "   Instala con: sudo apt install python3 python3-venv"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "   ✅ Python $PYTHON_VERSION encontrado"

# 2. Verificar Ollama
echo ""
echo "📦 Verificando Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "⚠️  Ollama NO está instalado"
    echo "   Instala con: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "   O descarga desde: https://ollama.ai/download"
    read -p "¿Continuar sin Ollama? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
else
    echo "   ✅ Ollama encontrado"
fi

# 3. Crear entorno virtual
echo ""
echo "🐍 Creando entorno virtual Python..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "   ✅ Entorno virtual creado"
else
    echo "   ✅ Entorno virtual ya existe"
fi

# Activar entorno virtual
source .venv/bin/activate

# 4. Instalar dependencias
echo ""
echo "📥 Instalando dependencias Python..."
pip install --upgrade pip
pip install -r requirements.txt
echo "   ✅ Dependencias instaladas"

# 5. Crear archivo .env si no existe
echo ""
echo "⚙️  Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "   ✅ Archivo .env creado"
    echo "   📝 Edita .env para personalizar la configuración"
else
    echo "   ✅ Archivo .env ya existe"
fi

# 6. Crear estructura de directorios
echo ""
echo "📁 Creando estructura de directorios..."
mkdir -p backend/dynamic_tools
mkdir -p frontend/src/assets
echo "   ✅ Directorios creados"

# 7. Instalar Node.js (frontend)
echo ""
echo "📦 Verificando Node.js..."
if ! command -v node &> /dev/null; then
    echo "⚠️  Node.js NO está instalado (solo necesario para frontend)"
    echo "   Instala con: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt install -y nodejs"
else
    NODE_VERSION=$(node --version)
    echo "   ✅ Node.js $NODE_VERSION encontrado"
fi

# 8. Descargar modelo de Ollama (opcional)
echo ""
read -p "¿Descargar modelo qwen2.5:1.5b? (s/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    if command -v ollama &> /dev/null; then
        echo "⏳ Descargando modelo (puede tardar varios minutos)..."
        ollama pull qwen2.5:1.5b
        echo "   ✅ Modelo descargado"
    else
        echo "❌ Ollama no está disponible"
    fi
fi

# Resumen final
echo ""
echo "✅ ============================================"
echo "   INSTALACIÓN COMPLETADA"
echo "============================================"
echo ""
echo "📝 Próximos pasos:"
echo ""
echo "1️⃣  Inicia Ollama en una terminal:"
echo "   ollama serve"
echo ""
echo "2️⃣  Activa el entorno virtual:"
echo "   source .venv/bin/activate"
echo ""
echo "3️⃣  Inicia el backend:"
echo "   cd backend"
echo "   export AGNUX_IA_PROVIDER=local"
echo "   export AGNUX_ACTIVE_MODEL=qwen2.5:1.5b"
echo "   python3 -m uvicorn app:app --reload --port 8000"
echo ""
echo "4️⃣  (Opcional) Inicia el frontend:"
echo "   cd frontend"
echo "   npm install"
echo "   npm start"
echo ""
echo "📚 Para más detalles:"
echo "   - Lee QUICKSTART.md"
echo "   - Lee README.md para documentación completa"
echo ""
echo "✅ ¡Listo! 🎉"
