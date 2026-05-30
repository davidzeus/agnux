import os
import logging
from dotenv import load_dotenv

# Cargar variables del entorno desde el archivo .env
load_dotenv()

# Configuraciones Globales
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://10.10.0.48:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "http://10.10.0.66:6333")
AGNUX_ACTIVE_MODEL = os.getenv("AGNUX_ACTIVE_MODEL", "ministral-es:latest")
AGNUX_CODER_MODEL = os.getenv("AGNUX_CODER_MODEL", "deepseek-coder:1.5b")

# Rutas estáticas del sistema
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DYNAMIC_DIR = os.path.join(BASE_DIR, "dynamic_tools")

# Crear el directorio dynamic_tools si no existe
os.makedirs(DYNAMIC_DIR, exist_ok=True)
if not os.path.exists(os.path.join(DYNAMIC_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_DIR, "__init__.py"), "w") as f:
        f.write("")

# Configurar Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AGNUX-CORE")
