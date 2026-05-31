# tools/sandbox_tool.py
# =====================================================================
# 🐳 AGNUX OS — MOTOR DE SANDBOX DOCKER (Code Evaluator)
# =====================================================================
# Ejecuta código en contenedores Docker efímeros, aislados y limitados.
# Soporta Python, JavaScript (Node) y Bash.
# El contenedor se crea, ejecuta y destruye en cada llamada.
# Sin acceso a red, sin escritura permanente, con límites de CPU/RAM.
# =====================================================================
import os
import time
import json
import tempfile
import logging

logger = logging.getLogger("AGNUX-SANDBOX")

# ── Configuración por lenguaje ────────────────────────────────────────
# Cada entrada define la imagen Docker, la extensión del archivo temporal
# y el comando de ejecución. Se usan imágenes Alpine (< 50MB) para
# mantener los tiempos de arranque por debajo de ~1-2 segundos cuando
# la imagen ya está en el cache local del daemon.
LANGUAGE_CONFIG: dict = {
    "python": {
        "image":   "python:3.11-alpine",
        "ext":     ".py",
        "cmd_fn":  lambda fname: ["python", "-u", fname],
    },
    "javascript": {
        "image":   "node:20-alpine",
        "ext":     ".js",
        "cmd_fn":  lambda fname: ["node", fname],
    },
    "js": {  # alias corto
        "image":   "node:20-alpine",
        "ext":     ".js",
        "cmd_fn":  lambda fname: ["node", fname],
    },
    "bash": {
        "image":   "alpine:latest",
        "ext":     ".sh",
        "cmd_fn":  lambda fname: ["sh", fname],
    },
    "shell": {
        "image":   "alpine:latest",
        "ext":     ".sh",
        "cmd_fn":  lambda fname: ["sh", fname],
    },
}

# Límites de seguridad del sandbox
SANDBOX_MEMORY_LIMIT = "128m"       # RAM máxima por contenedor
SANDBOX_CPU_QUOTA    = 50_000       # 0.5 CPU (50% de 1 core)
SANDBOX_CPU_PERIOD   = 100_000      # Period base para cálculo de cuota
SANDBOX_TIMEOUT_SEC  = 20           # Timeout de ejecución
SANDBOX_MAX_OUTPUT   = 8_000        # Máximo de bytes de output capturado


def ejecutar_en_docker_sync(codigo: str, lenguaje: str) -> dict:
    """
    Función SÍNCRONA que lanza un contenedor Docker efímero, ejecuta el
    código y retorna el resultado estructurado.

    Esta función es llamada desde un thread separado por asyncio.to_thread
    para no bloquear el event loop de FastAPI.

    Retorna un dict con:
      ok            (bool)   - True si exit_code == 0
      exit-code     (int)    - Código de salida del proceso
      output        (str)    - stdout + stderr combinados
      error-detail  (str)    - Descripción del error si ok=False
      execution-ms  (int)    - Tiempo de ejecución en ms
      language      (str)    - Lenguaje ejecutado
    """
    lang_key = lenguaje.strip().lower()
    config   = LANGUAGE_CONFIG.get(lang_key)

    if config is None:
        lenguajes_soportados = ", ".join(LANGUAGE_CONFIG.keys())
        return {
            "ok":           False,
            "exit-code":    -1,
            "output":       "",
            "error-detail": f"Lenguaje '{lenguaje}' no soportado. Lenguajes válidos: {lenguajes_soportados}",
            "execution-ms": 0,
            "language":     lenguaje,
        }

    try:
        import docker  # Importación diferida: no falla el startup si Docker no está
        from docker.errors import ContainerError, ImageNotFound, APIError
    except ImportError:
        return {
            "ok":           False,
            "exit-code":    -1,
            "output":       "",
            "error-detail": "El SDK de Docker no está instalado. Ejecutar: pip install docker>=7.0.0",
            "execution-ms": 0,
            "language":     lenguaje,
        }

    # Crear archivo temporal con el código dentro de /tmp del HOST
    # (será montado como volumen read-only dentro del contenedor)
    tmp_file = None
    t0 = time.monotonic()
    container = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=config["ext"],
            delete=False,
            encoding="utf-8",
            prefix="agnux_sandbox_"
        ) as tf:
            tf.write(codigo)
            tmp_file = tf.name

        client    = docker.from_env()
        fname_in  = f"/sandbox/code{config['ext']}"
        cmd       = config["cmd_fn"](fname_in)

        logger.info(
            f"🐳 [SANDBOX] Lanzando contenedor '{config['image']}' para código {lang_key} "
            f"({len(codigo)} chars)..."
        )

        # Verificar que la imagen existe localmente; si no, intentar pull
        try:
            client.images.get(config["image"])
        except docker.errors.ImageNotFound:
            logger.info(f"📥 [SANDBOX] Imagen '{config['image']}' no encontrada. Haciendo pull...")
            client.images.pull(config["image"])

        container = client.containers.run(
            image        = config["image"],
            command      = cmd,
            volumes      = {tmp_file: {"bind": fname_in, "mode": "ro"}},
            # ── Aislamiento total ─────────────────────────────────────
            network_mode = "none",           # Sin acceso a internet
            read_only    = True,             # Filesystem de solo lectura
            tmpfs        = {"/tmp": "size=16m,noexec"},  # /tmp en RAM
            # ── Límites de recursos ───────────────────────────────────
            mem_limit        = SANDBOX_MEMORY_LIMIT,
            memswap_limit    = SANDBOX_MEMORY_LIMIT,    # Sin swap
            cpu_period       = SANDBOX_CPU_PERIOD,
            cpu_quota        = SANDBOX_CPU_QUOTA,
            # ── Seguridad adicional ───────────────────────────────────
            security_opt     = ["no-new-privileges"],
            cap_drop         = ["ALL"],
            # ── Lifecycle ─────────────────────────────────────────────
            detach           = False,
            remove           = True,         # Auto-destruye al terminar
            stdout           = True,
            stderr           = True,
            timeout          = SANDBOX_TIMEOUT_SEC,
        )

        elapsed_ms = int((time.monotonic() - t0) * 1000)

        # `container` es bytes cuando detach=False
        raw_output = container.decode("utf-8", errors="replace") if isinstance(container, bytes) else str(container)
        raw_output = raw_output[:SANDBOX_MAX_OUTPUT]

        logger.info(f"✅ [SANDBOX] Ejecución completada en {elapsed_ms}ms. exit_code=0")
        return {
            "ok":           True,
            "exit-code":    0,
            "output":       raw_output,
            "error-detail": "",
            "execution-ms": elapsed_ms,
            "language":     lang_key,
        }

    except Exception as e:
        elapsed_ms = int((time.monotonic() - t0) * 1000)

        # Distinguir entre error de código (ContainerError) y error de infra
        try:
            from docker.errors import ContainerError
            if isinstance(e, ContainerError):
                stderr_output = e.stderr.decode("utf-8", errors="replace") if e.stderr else str(e)
                stderr_output = stderr_output[:SANDBOX_MAX_OUTPUT]
                exit_code     = e.exit_status
                logger.warning(f"⚠️ [SANDBOX] Código falló con exit_code={exit_code}: {stderr_output[:200]}")
                return {
                    "ok":           False,
                    "exit-code":    exit_code,
                    "output":       stderr_output,
                    "error-detail": f"El código terminó con error (exit_code={exit_code}).",
                    "execution-ms": elapsed_ms,
                    "language":     lang_key,
                }
        except ImportError:
            pass

        # Error de infraestructura (daemon Docker caído, timeout, etc.)
        logger.error(f"❌ [SANDBOX] Error de infraestructura Docker: {e}")
        return {
            "ok":           False,
            "exit-code":    -2,
            "output":       "",
            "error-detail": f"Error de infraestructura Docker: {str(e)}",
            "execution-ms": elapsed_ms,
            "language":     lang_key,
        }

    finally:
        # Garantizar limpieza del archivo temporal del host
        if tmp_file and os.path.exists(tmp_file):
            try:
                os.unlink(tmp_file)
            except Exception:
                pass
        # Si el contenedor no se auto-destruyó (detach=True fallback), forzar remoción
        if container is not None and not isinstance(container, bytes):
            try:
                container.remove(force=True)
            except Exception:
                pass
