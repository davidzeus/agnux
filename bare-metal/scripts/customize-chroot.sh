#!/bin/bash
# =====================================================================
# 🧬 AGNUX OS v2.0 - CHROOT CUSTOMIZATION RUNNER
# =====================================================================
set -e

echo "🟩 [CHROOT] Iniciando personalización interna de la ISO raíz..."

# Configurar DNS temporal para la descarga de paquetes
echo "nameserver 1.1.1.1" > /etc/resolv.conf
echo "nameserver 8.8.8.8" >> /etc/resolv.conf

# 1. Actualizar repositorios e instalar dependencias básicas
apt-get update

# Instalar herramientas gráficas, el compositor Wayland cage y bibliotecas de PySide6
apt-get install -y \
    cage \
    libwayland-client0 \
    libwayland-egl1 \
    libxkbcommon0 \
    python3-pip \
    python3-venv \
    python3-pyside6.qtwebenginewidgets \
    python3-pyside6.qtwidgets \
    python3-pyside6.qtgui \
    python3-pyside6.qtcore \
    libgl1 \
    xterm \
    galculator \
    pcmanfm \
    curl \
    git \
    nginx \
    psmisc

# 2. Instalar soporte de aceleración gráfica NVIDIA (Drivers privativos y utilities)
echo "📦 Instalando controladores NVIDIA para aceleración CUDA en el live environment..."
apt-get install -y nvidia-driver-535 nvidia-utils-535 || apt-get install -y nvidia-driver || echo "⚠️ Falló la instalación automática de NVIDIA. Continuando..."

# 3. Instalar Docker Engine para el Sandbox y Qdrant
if ! command -v docker &> /dev/null; then
    echo "📦 Instalando Docker Engine..."
    curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
    sh /tmp/get-docker.sh || true
    rm -f /tmp/get-docker.sh
fi

# 4. Crear el entorno virtual del backend e instalar los requerimientos
echo "🐍 Inicializando entorno virtual Python en /opt/agnux/backend/venv..."
cd /opt/agnux/backend
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# 5. Configurar Nginx como proxy reverso para la API y la UI
echo "🌐 Configurando Nginx..."
cat << 'EOF' > /etc/nginx/sites-available/default
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

# 6. Crear la sesión gráfica Wayland para "AGNUX OS" en SDDM
echo "🎨 Registrando la sesión de escritorio Wayland de AGNUX..."
mkdir -p /usr/share/wayland-sessions
cat << 'EOF' > /usr/share/wayland-sessions/agnux.desktop
[Desktop Entry]
Name=AGNUX OS
Comment=AGNUX OS Cognitive Shell v2.0
Exec=/usr/local/bin/start-agnux-session.sh
Type=Application
DesktopNames=AGNUX
EOF

# 7. Crear el script de arranque global de la sesión
echo "⚙️ Configurando el script de inicio global /usr/local/bin/start-agnux-session.sh..."
cat << 'EOF' > /usr/local/bin/start-agnux-session.sh
#!/bin/bash
# =====================================================================
# 🚀 AGNUX OS SESSION LAUNCHER
# =====================================================================

# Iniciar servicios esenciales
systemctl start nginx || service nginx start || true
systemctl start docker || service docker start || true

# Asegurar que Qdrant esté corriendo en Docker
if command -v docker &> /dev/null; then
    docker start qdrant || docker run -d --name qdrant \
        --restart always \
        -p 6333:6333 \
        -v /var/lib/qdrant:/qdrant/storage \
        qdrant/qdrant:latest || true
fi

# Arrancar el backend de AGNUX
cd /opt/agnux/backend
/opt/agnux/backend/venv/bin/python -m uvicorn main:app --port 8000 --host 127.0.0.1 > /tmp/agnux-backend.log 2>&1 &

# Esperar a que el backend esté listo
sleep 2.5

# Entorno Qt para Wayland
export QT_QPA_PLATFORM=wayland
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1
export AGNUX_KIOSK=1

# Lanzar el cliente gráfico PySide6 dentro del compositor Wayland cage
# (cage bloquea la sesión de SDDM hasta que la shell termina)
cd /opt/agnux/desktop
exec cage -s -- /opt/agnux/backend/venv/bin/python shell.py > /tmp/agnux-desktop.log 2>&1
EOF

chmod +x /usr/local/bin/start-agnux-session.sh

# 8. Forzar autologin de la sesión "agnux" en el gestor SDDM
echo "🔒 Configurando autologin por defecto en SDDM a la sesión de AGNUX..."
mkdir -p /etc/sddm.conf.d

cat << 'EOF' > /etc/sddm.conf.d/agnux.conf
[Autologin]
Session=agnux.desktop

[LastSession]
Session=agnux.desktop
EOF

cat << 'EOF' > /etc/sddm.conf
[Autologin]
Session=agnux.desktop

[LastSession]
Session=agnux.desktop
EOF

echo "🟩 [CHROOT] Personalización completada con éxito."
