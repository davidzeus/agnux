.PHONY: all iso clean

all: iso

iso:
	@echo "💿 Compilando entorno de distribución AGNUX OS..."
	bash build-iso.sh

clean:
	@echo "🧹 Limpiando directorios temporales de compilación..."
	sudo rm -rf ./mnt ./custom_iso ./squashfs_root
	@echo "✨ Directorio limpio."