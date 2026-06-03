#!/bin/bash
# =====================================================================
# 🚀 AGNUX OS CORE v2.0 - BARE-METAL PROVISIONING SCRIPT
# =====================================================================
set -e

echo "🟩 [AGNUX BOOTSTRAP] Iniciando aprovisionamiento del sistema operativo..."

# 1. Actualizar repositorios e instalar dependencias gráficas y de sistema base
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y \
    xorg \
    openbox \
    python3-pip \
    python3-venv \
    curl \
    git \
    psmisc \
    nginx \
    libgl1-mesa-glx \
    libegl1-mesa \
    libxrender1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxtst6 \
    libasound2 \
    libnss3 \
    libnspr4 \
    libxcb1 \
    libxkbcommon-x11-0 \
    libfontconfig1 \
    libdbus-1-3

# 2. Instalar el motor Docker para soporte de Sandbox y Qdrant
if ! command -v docker &> /dev/null; then
    echo "📦 [AGNUX CORE] Instalando Docker Engine para aislamiento de micro-dockers..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Iniciar Docker
sudo systemctl enable docker
sudo systemctl start docker

# 3. Descargar imágenes de Docker esenciales en caché offline
echo "🐳 [AGNUX CORE] Descargando imagen de sandbox (python:3.11-alpine)..."
sudo docker pull python:3.11-alpine

echo "🐳 [AGNUX CORE] Descargando y ejecutando Qdrant Vector DB en Docker..."
sudo docker pull qdrant/qdrant:latest
if [ ! "$(sudo docker ps -q -f name=qdrant)" ]; then
    if [ "$(sudo docker ps -aq -f name=qdrant)" ]; then
        sudo docker rm -f qdrant
    fi
    sudo docker run -d --name qdrant \
        --restart always \
        -p 6333:6333 \
        -v /var/lib/qdrant:/qdrant/storage \
        qdrant/qdrant:latest
fi

# 4. Configurar Nginx como proxy reverso para assets estáticos y endpoints de API
echo "🌐 [AGNUX CORE] Configurando Nginx para servir el frontend de AGNUX..."
sudo tee /etc/nginx/sites-available/default << 'EOF'
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /opt/agnux/frontend;
    index index.html;

    server_name _;

    location / {
        try_files $uri $uri/ =404;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
    }
}
EOF
sudo systemctl restart nginx

# 5. Configurar el inicio automático de X11 sin entorno GNOME/KDE
echo "🎨 [AGNUX CORE] Configurando sesión gráfica minimalista (Modo Kiosco)..."
mkdir -p ~/.config/openbox
cp /opt/agnux/bare-metal/config/openbox-autostart ~/.config/openbox/autostart
chmod +x ~/.config/openbox/autostart

# 6. Crear entorno virtual del backend e instalar requerimientos
echo "🐍 [AGNUX CORE] Configurando entorno virtual de python..."
cd /opt/agnux/backend
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Habilitar servicio del core en systemd
sudo cp /opt/agnux/bare-metal/config/agnux-core.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable agnux-core.service
sudo systemctl start agnux-core.service

echo "✅ [AGNUX BOOTSTRAP] Configuración completada. AGNUX OS está listo para el primer booteo nativo."
