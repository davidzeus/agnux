#!/bin/bash
# =====================================================================
# 🚀 AGNUX OS - SESSION LAUNCHER (OFFLINE & LIVE FRIENDLY)
# =====================================================================

# Iniciar servicios esenciales
echo "🟢 [AGNUX LAUNCHER] Iniciando servicios del sistema..."
sudo systemctl start nginx || sudo service nginx start || true
sudo systemctl start docker || sudo service docker start || true

# Cargar la imagen de docker de Qdrant si no está presente localmente
if command -v docker &> /dev/null; then
    if ! sudo docker image inspect qdrant/qdrant:latest &> /dev/null; then
        echo "📦 [AGNUX LAUNCHER] Cargando base de datos vectoriales Qdrant sin conexión..."
        if [ -f /opt/agnux/qdrant.tar ]; then
            sudo docker load -i /opt/agnux/qdrant.tar
        fi
    fi

    # Asegurar que Qdrant esté corriendo en Docker
    echo "📦 [AGNUX LAUNCHER] Inicializando Qdrant DB..."
    sudo docker start qdrant || sudo docker run -d --name qdrant \
        --restart always \
        -p 6333:6333 \
        -v /var/lib/qdrant:/qdrant/storage \
        qdrant/qdrant:latest || true
fi

# Arrancar el backend de AGNUX
echo "🐍 [AGNUX LAUNCHER] Arrancando servidor Python backend..."
cd /opt/agnux/backend
/opt/agnux/backend/venv/bin/python -m uvicorn main:app --port 8000 --host 127.0.0.1 > /tmp/agnux-backend.log 2>&1 &

# Arrancar el gestor de ventanas openbox (en segundo plano)
echo "🎨 [AGNUX LAUNCHER] Iniciando gestor de ventanas Openbox..."
openbox &

# Esperar a que el backend de Uvicorn responda
echo "⏳ [AGNUX LAUNCHER] Esperando inicialización de la API..."
sleep 3.5

# Lanzar el cliente gráfico PySide6 (bloquea la sesión de SDDM)
echo "🖥️ [AGNUX LAUNCHER] Lanzando interface cognitiva shell..."
cd /opt/agnux/desktop
/opt/agnux/backend/venv/bin/python shell.py > /tmp/agnux-desktop.log 2>&1
