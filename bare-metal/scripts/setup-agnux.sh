#!/bin/bash
# =====================================================================
# 🚀 AGNUX OS CORE - BARE-METAL PROVISIONING SCRIPT
# =====================================================================
set -e

echo "🟩 [AGNUX BOOTSTRAP] Iniciando aprovisionamiento del sistema operativo sobre los fierros..."

# 1. Actualizar repositorios e instalar dependencias del sistema base
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y \
    xorg \
    openbox \
    chromium-browser \
    python3-pip \
    python3-venv \
    curl \
    git \
    psmisc

# 2. Inyectar motor Docker local (Esencial para tu pipeline de Sandbox estilo Claude)
if ! command -v docker &> /dev/null; then
    echo "📦 [AGNUX CORE] Instalando Docker Engine para aislamiento de micro-dockers..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# 3. Descargar imagen base Alpine para el testing en caliente (Dejala en caché para que vuele en 0.05s)
sudo docker pull python:3.11-alpine

# 4. Configurar el inicio automático de X11 sin entorno GNOME/KDE
echo "🎨 [AGNUX CORE] Configurando sesión gráfica minimalista (Modo Kiosco)..."
mkdir -p ~/.config/openbox

# Creamos el autostart de Openbox para levantar el Backend y luego lanzar Chromium maximizado
cat << 'EOF' > ~/.config/openbox/autostart
# Levantar el bus del backend de Python
cd /opt/agnux/backend && ./venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 &

# Esperar a que el Kernel de AGNUX esté vivo
sleep 3

# Lanzar tu interfaz gráfica en Angular embebida a pantalla completa
chromium-browser \
    --kiosk \
    --app=http://localhost:4200 \
    --no-first-run \
    --no-default-browser-check \
    --disable-infobars \
    --disable-session-crashed-bubble \
    --overscroll-history-navigation=0 \
    --user-data-dir=~/.config/agnux/browser_session &
EOF

echo "✅ [AGNUX BOOTSTRAP] Configuración completada. AGNUX OS está listo para el primer booteo nativo."