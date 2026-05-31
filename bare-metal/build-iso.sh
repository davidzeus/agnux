#!/bin/bash
# =====================================================================
# 💿 AGNUX OS - ISO COMPILER SCRIPT (BARE-METAL DISTRO DEBIAN/ROOT)
# =====================================================================
set -e

IMAGE_NAME="agnux-os-installer.iso"
UBUNTU_ISO_URL="https://releases.ubuntu.com/24.04.1/ubuntu-24.04.1-live-server-amd64.iso"

echo "🟩 [AGNUX COMPILER] Iniciando la creación de la ISO como ROOT..."

# 1. Instalar herramientas de empaquetado si faltan (Nativo de Debian)
apt-get update && apt-get install -y xorriso squashfs-tools wget

# 2. Descargar la ISO base oficial de Ubuntu Server
if [ ! -f "ubuntu-base.iso" ]; then
    echo "📥 Descargando ISO base de Ubuntu Server..."
    wget -O ubuntu-base.iso "$UBUNTU_ISO_URL"
fi

# 3. Crear directorios de trabajo y extraer la ISO
mkdir -p ./mnt ./custom_iso ./squashfs_root
mount -o loop ubuntu-base.iso ./mnt
cp -r ./mnt/* ./custom_iso/
cp -r ./mnt/.disk/ ./custom_iso/
umount ./mnt

# 4. Extraer el sistema de archivos raíz (SquashFS)
echo "📦 Extrayendo SquashFS..."
unsquashfs -d ./squashfs_root ./custom_iso/casper/filesystem.squashfs

# =====================================================================
# 🧬 INYECCIÓN DEL NÚCLEO AGNUX (RUTAS CORREGIDAS Y ORDENADAS)
# =====================================================================
echo "🚀 Inyectando componentes estructurados de AGNUX..."

# Copiar backend y frontend al sistema raíz de la ISO
mkdir -p ./squashfs_root/opt/agnux
cp -r ../backend ../frontend ./squashfs_root/opt/agnux/

# 📁 1. Inyectar configuraciones de sistema desde ./config
cp ./config/agnux-core.service ./squashfs_root/etc/systemd/system/
mkdir -p ./squashfs_root/root/.config/openbox
cp ./config/openbox-autostart ./squashfs_root/root/.config/openbox/autostart

# 📁 2. Configurar scripts de inicialización desde ./scripts
cp ./scripts/setup-agnux.sh ./squashfs_root/etc/rc.local
chmod +x ./squashfs_root/etc/rc.local

# 📁 3. Customizar menú de arranque si existe customización en ./boot
if [ -f "./boot/grub.cfg" ]; then
    cp ./boot/grub.cfg ./custom_iso/boot/grub/grub.cfg
fi

# =====================================================================
# 💿 RE-EMPAQUETADO Y SELLADO
# =====================================================================
echo "🔒 Sellando y comprimiendo el sistema de archivos..."
rm -f ./custom_iso/casper/filesystem.squashfs
mksquashfs ./squashfs_root ./custom_iso/casper/filesystem.squashfs -comp xz

cd ./custom_iso
find . -type f -print0 | xargs -0 md5sum | grep -v "boot.cat" | grep -v "md5sum.txt" > md5sum.txt
cd ..

echo "💿 Generando archivo ISO definitivo..."
xorriso -as mkisofs \
    -r -V "AGNUX_OS" \
    -o "$IMAGE_NAME" \
    -J -joliet-long \
    -b biosbits/biosbits.cfg \
    -c boot.cat \
    -boot-load-size 4 -boot-info-table -no-emul-boot \
    -eltorito-alt-boot \
    -e boot/grub/efi.img \
    -no-emul-boot \
    ./custom_iso

echo "✅ [AGNUX COMPILER] Proceso completado con éxito."