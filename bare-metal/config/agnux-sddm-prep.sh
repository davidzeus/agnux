#!/bin/bash
# =====================================================================
# ⚙️ AGNUX OS - SDDM AUTOLOGIN & PERMISSIONS ENFORCER
# =====================================================================

# Detectar el usuario live real (UID 999 suele ser el por defecto en Casper)
LIVE_USER=$(grep -E '^[^:]+:[^:]+:999:' /etc/passwd | cut -d: -f1)
if [ -z "$LIVE_USER" ]; then
    LIVE_USER="neon" # Fallback por si acaso
fi

echo "🟢 [AGNUX PREP] Configurando autologin para el usuario: $LIVE_USER con sesión: agnux.desktop"

# Cambiar propiedad de la carpeta del proyecto al usuario live para escritura de SQLite/logs
if [ -d /opt/agnux ]; then
    chown -R $LIVE_USER:$LIVE_USER /opt/agnux
fi

# Crear directorio de configuración de SDDM si no existe
mkdir -p /etc/sddm.conf.d

# Escribir la configuración de autologin forzada
cat << EOF > /etc/sddm.conf.d/agnux.conf
[Autologin]
User=$LIVE_USER
Session=agnux.desktop

[LastSession]
Session=agnux.desktop
EOF

cat << EOF > /etc/sddm.conf
[Autologin]
User=$LIVE_USER
Session=agnux.desktop

[LastSession]
Session=agnux.desktop
EOF

echo "🟢 [AGNUX PREP] Configuración de SDDM y permisos de /opt/agnux listos."
