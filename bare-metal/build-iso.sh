#!/bin/bash
# =====================================================================
# 💿 AGNUX OS v2.0 - ISO COMPILER SCRIPT (KDE NEON CUSTOMIZER)
# =====================================================================
set -e

IMAGE_NAME="agnux-os-neon-v2.0.iso"
BASE_ISO="neon-user-current.iso"

echo "🟩 [AGNUX COMPILER] Iniciando la creación de la ISO como ROOT..."

# 1. Asegurar herramientas de empaquetado y p7zip en la máquina host
sudo apt-get update && sudo apt-get install -y xorriso squashfs-tools wget p7zip-full

# 2. Verificar que la ISO base de KDE Neon existe
if [ ! -f "$BASE_ISO" ]; then
    echo "❌ Error: No se encuentra la ISO base de KDE Neon '$BASE_ISO' en el directorio."
    exit 1
fi

# 3. Limpiar compilaciones previas si existen
echo "🧹 Limpiando directorios temporales de compilación..."
sudo rm -rf ./custom_iso ./squashfs_root

# 4. Extracción de la estructura ISO base usando 7z
echo "📦 Extrayendo estructura ISO base..."
mkdir -p ./custom_iso ./squashfs_root
7z x "$BASE_ISO" -o./custom_iso/ -y

# 5. Buscar y extraer el sistema de archivos raíz SquashFS dinámicamente
SQUASHFS_FILE=$(find ./custom_iso -name "*.squashfs" | head -n 1)
if [ -z "$SQUASHFS_FILE" ]; then
    echo "❌ Error: No se encontró ningún archivo SquashFS (.squashfs) en la estructura ISO."
    exit 1
fi

echo "📦 Extrayendo sistema de archivos SquashFS desde: $SQUASHFS_FILE ..."
sudo unsquashfs -d ./squashfs_root "$SQUASHFS_FILE"

# =====================================================================
# 🧬 INYECCIÓN DEL NÚCLEO AGNUX v2.0
# =====================================================================
echo "🚀 Inyectando componentes estructurados de AGNUX v2.0..."

# Crear directorio de instalación de AGNUX
sudo mkdir -p ./squashfs_root/opt/agnux

# Copiar directorios de código fuente (backend, frontend, desktop)
sudo cp -r ../backend ./squashfs_root/opt/agnux/
sudo cp -r ../frontend ./squashfs_root/opt/agnux/
sudo cp -r ../desktop ./squashfs_root/opt/agnux/

# Copiar directorios de bare-metal
sudo mkdir -p ./squashfs_root/opt/agnux/bare-metal
sudo cp -r ../bare-metal/boot ./squashfs_root/opt/agnux/bare-metal/
sudo cp -r ../bare-metal/config ./squashfs_root/opt/agnux/bare-metal/
sudo cp -r ../bare-metal/scripts ./squashfs_root/opt/agnux/bare-metal/
sudo cp ../bare-metal/build-iso.sh ./squashfs_root/opt/agnux/bare-metal/

# Crear archivo .env limpio (sin claves secretas de la sesión actual)
echo "🔒 Creando configuración .env libre de credenciales privadas..."
sudo tee ./squashfs_root/opt/agnux/backend/.env << 'EOF'
iaProvider=local
ollamaHost=http://127.0.0.1:11434
qdrantHost=http://127.0.0.1:6333
agnuxActiveModel=qwen2.5-coder:7b
agnuxCoderModel=qwen2.5-coder:7b
geminiApiKey=
openaiApiKey=
backendPort=8000
backendHost=127.0.0.1
googleClientId=
googleClientSecret=
numGpu=1
EOF

# =====================================================================
# 🛠️ EJECUCIÓN DEL CONFIGURADOR CHROOT
# =====================================================================
echo "🔧 Ejecutando personalizador chroot de AGNUX OS..."
sudo cp ./scripts/customize-chroot.sh ./squashfs_root/tmp/
sudo chmod +x ./squashfs_root/tmp/customize-chroot.sh

# Montar directorios necesarios para el chroot
sudo mount --bind /dev ./squashfs_root/dev
sudo mount --bind /dev/pts ./squashfs_root/dev/pts
sudo mount --bind /proc ./squashfs_root/proc
sudo mount --bind /sys ./squashfs_root/sys

# Ejecutar el chroot
sudo chroot ./squashfs_root /bin/bash /tmp/customize-chroot.sh

# Desmontar directorios
sudo umount ./squashfs_root/dev/pts || true
sudo umount ./squashfs_root/dev || true
sudo umount ./squashfs_root/proc || true
sudo umount ./squashfs_root/sys || true

# Limpiar script temporal
sudo rm -f ./squashfs_root/tmp/customize-chroot.sh

# =====================================================================
# 💿 RE-EMPAQUETADO DE LA ISO
# =====================================================================
echo "🔒 Sellando y comprimiendo el nuevo sistema de archivos SquashFS..."
sudo rm -f "$SQUASHFS_FILE"
sudo mksquashfs ./squashfs_root "$SQUASHFS_FILE" -comp xz

# Regenerar firmas de integridad md5
cd ./custom_iso
find . -type f -print0 | xargs -0 md5sum | grep -v "boot.cat" | grep -v "md5sum.txt" > md5sum.txt || true
cd ..

echo "💿 Generando archivo ISO híbrido definitivo de AGNUX OS..."
if [ -f "./custom_iso/boot/grub/i386-pc/eltorito.img" ]; then
    echo "Found GRUB boot loader."
    sudo xorriso -as mkisofs \
        -r -V "AGNUX_OS" \
        -o "$IMAGE_NAME" \
        -J -joliet-long \
        -b boot/grub/i386-pc/eltorito.img \
        -c boot.catalog \
        -boot-load-size 4 -boot-info-table -no-emul-boot \
        -eltorito-alt-boot \
        -e '[BOOT]/1-Boot-NoEmul.img' \
        -no-emul-boot \
        -isohybrid-gpt-basdat \
        ./custom_iso
elif [ -f "./custom_iso/isolinux/isolinux.bin" ]; then
    echo "Found isolinux boot loader."
    sudo xorriso -as mkisofs \
        -r -V "AGNUX_OS" \
        -o "$IMAGE_NAME" \
        -J -joliet-long \
        -b isolinux/isolinux.bin \
        -c isolinux/boot.cat \
        -boot-load-size 4 -boot-info-table -no-emul-boot \
        -eltorito-alt-boot \
        -e boot/grub/efi.img \
        -no-emul-boot \
        -isohybrid-gpt-basdat \
        ./custom_iso
else
    echo "No boot files matched. Generating standard ISO..."
    sudo xorriso -as mkisofs -r -V "AGNUX_OS" -o "$IMAGE_NAME" -J -joliet-long ./custom_iso
fi

echo "✅ [AGNUX COMPILER] ISO compilada con éxito: $IMAGE_NAME"
