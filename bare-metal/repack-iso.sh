#!/bin/bash
# =====================================================================
# 💿 AGNUX OS - QUICK ISO REPACKAGING SCRIPT
# =====================================================================
set -e

CWD="/home/david/Documentos/agnuxV2/bare-metal"
cd "$CWD"

IMAGE_NAME="agnux-os-neon-v2.0.iso"
SQUASHFS_FILE="./custom_iso/casper/filesystem.squashfs"

# 1. Asegurar que desmontamos todo por si acaso
echo "🧹 Desmontando virtual filesystems por seguridad..."
sudo umount -lf ./squashfs_root/dev/pts || true
sudo umount -lf ./squashfs_root/dev || true
sudo umount -lf ./squashfs_root/proc || true
sudo umount -lf ./squashfs_root/sys || true

# Asegurar que el directorio de destino para el squashfs existe
mkdir -p "$(dirname "$SQUASHFS_FILE")"

# 2. Compresión condicional de SquashFS
if [ -f "$SQUASHFS_FILE" ]; then
    echo "⚡ [AGNUX COMPILER] El archivo SquashFS ya existe en: $SQUASHFS_FILE"
    echo "⚡ Saltando compresión para ahorrar tiempo..."
else
    # Copiar scripts de autologin y habilitar servicio systemd
    echo "🚀 Copiando configuraciones de autologin de SDDM al SquashFS..."
    sudo mkdir -p ./squashfs_root/usr/local/bin
    sudo cp ./config/agnux-sddm-prep.sh ./squashfs_root/usr/local/bin/agnux-sddm-prep.sh
    sudo chmod +x ./squashfs_root/usr/local/bin/agnux-sddm-prep.sh

    sudo mkdir -p ./squashfs_root/etc/systemd/system/graphical.target.wants
    sudo cp ./config/agnux-sddm-prep.service ./squashfs_root/etc/systemd/system/agnux-sddm-prep.service
    sudo ln -sf /etc/systemd/system/agnux-sddm-prep.service ./squashfs_root/etc/systemd/system/graphical.target.wants/agnux-sddm-prep.service

    # Copiar script de arranque global y base de datos offline Qdrant
    echo "🚀 Copiando script de arranque global y base de datos Qdrant offline..."
    sudo cp ./config/start-agnux-session.sh ./squashfs_root/usr/local/bin/start-agnux-session.sh
    sudo chmod +x ./squashfs_root/usr/local/bin/start-agnux-session.sh

    sudo mkdir -p ./squashfs_root/opt/agnux
    sudo cp ./config/qdrant.tar ./squashfs_root/opt/agnux/qdrant.tar

    echo "🔒 Comprimiendo el nuevo sistema de archivos SquashFS con GZIP (para mayor rapidez)..."
    sudo rm -f "$SQUASHFS_FILE"
    sudo mksquashfs ./squashfs_root "$SQUASHFS_FILE" -comp gzip
fi

# Regenerar firmas de integridad md5
echo "✍️ Regenerando firmas md5..."
cd ./custom_iso
find . -type f -print0 | xargs -0 md5sum | grep -v "boot.cat" | grep -v "md5sum.txt" > md5sum.txt || true
cd ..

echo "💿 Generando archivo ISO híbrido definitivo de AGNUX OS (con soporte para archivos >4GB)..."
if [ -f "./custom_iso/boot/grub/i386-pc/eltorito.img" ]; then
    echo "Found GRUB boot loader."
    sudo xorriso -as mkisofs \
        -iso-level 3 \
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
        -iso-level 3 \
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
    sudo xorriso -as mkisofs -iso-level 3 -r -V "AGNUX_OS" -o "$IMAGE_NAME" -J -joliet-long ./custom_iso
fi

echo "✅ [AGNUX COMPILER] ISO compilada con éxito y optimizada: $IMAGE_NAME"
