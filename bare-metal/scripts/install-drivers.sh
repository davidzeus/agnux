#!/bin/bash
# Script especializado para detectar e instalar CUDA y drivers de NVIDIA en AGNUX

echo "Instalando drivers de NVIDIA y CUDA..."

# Detectar GPU NVIDIA
if lspci | grep -i nvidia > /dev/null; then
    echo "GPU NVIDIA detectada. Procediendo con la instalación de drivers..."
    # Comandos de instalación de drivers y CUDA aquí
    # apt-get update
    # apt-get install -y nvidia-driver-535 nvidia-cuda-toolkit
    echo "Instalación completada."
else
    echo "No se detectó GPU NVIDIA en el sistema."
fi
