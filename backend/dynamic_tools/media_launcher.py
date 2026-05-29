import os
import subprocess
import asyncio
import logging

logger = logging.getLogger("AgnuxMediaKiosk")

async def launch_chromium_kiosk(platform: str):
    """
    Lanza un subproceso de Chromium en modo app (kiosco) aislado.
    Se persiste la sesión en un directorio único para cada plataforma.
    """
    platform_urls = {
        "spotify": "https://open.spotify.com",
        "youtubeMusic": "https://music.youtube.com",
        "netflix": "https://www.netflix.com"
    }

    url = platform_urls.get(platform)
    if not url:
        logger.error(f"❌ Plataforma desconocida: {platform}")
        return

    # Expandir el tilde (~) para asegurar la ruta correcta en cualquier OS
    user_data_dir = os.path.expanduser(f"~/.config/agnux/apps/{platform}")
    os.makedirs(user_data_dir, exist_ok=True)

    # Rutas típicas del ejecutable de Chromium / Chrome según el OS
    # Nota: Este código asume Linux, para Windows podría necesitarse "chrome.exe"
    chrome_binaries = [
        "chromium",
        "chromium-browser",
        "google-chrome",
        "google-chrome-stable",
        # Rutas comunes en Windows por si acaso
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]

    chrome_cmd = None
    for bin_path in chrome_binaries:
        # Check in path or check exact path
        import shutil
        if shutil.which(bin_path) or os.path.exists(bin_path):
            chrome_cmd = shutil.which(bin_path) or bin_path
            break

    if not chrome_cmd:
        logger.error("❌ No se encontró el binario de Chromium/Chrome en el sistema.")
        return

    flags = [
        chrome_cmd,
        f"--app={url}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check"
    ]

    logger.info(f"🎵 [MEDIA LAUNCHER] Lanzando kiosco para {platform}: {url}")
    try:
        # Se lanza como un subproceso desvinculado
        process = await asyncio.create_subprocess_exec(
            *flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"🚀 Proceso Chromium iniciado con PID {process.pid}")
    except Exception as e:
        logger.error(f"❌ Error al lanzar Chromium: {e}")
