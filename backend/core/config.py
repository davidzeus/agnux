import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global configurations in camelCase
iaProvider = os.getenv("iaProvider", os.getenv("AGNUX_IA_PROVIDER", "local"))
ollamaHost = os.getenv("ollamaHost", os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
qdrantHost = os.getenv("qdrantHost", os.getenv("QDRANT_HOST", "http://127.0.0.1:6333"))
sqliteDbPath = os.getenv("sqliteDbPath", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "local.db"))
agnuxActiveModel = os.getenv("agnuxActiveModel", os.getenv("AGNUX_ACTIVE_MODEL", "qwen2.5-coder:7b"))
agnuxCoderModel = os.getenv("agnuxCoderModel", os.getenv("AGNUX_CODER_MODEL", "qwen2.5-coder:7b"))
geminiApiKey = os.getenv("geminiApiKey", os.getenv("GEMINI_API_KEY", ""))
openaiApiKey = os.getenv("openaiApiKey", os.getenv("OPENAI_API_KEY", ""))
backendPort = int(os.getenv("backendPort", os.getenv("BACKEND_PORT", "8000")))
backendHost = os.getenv("backendHost", os.getenv("BACKEND_HOST", "127.0.0.1"))

# Google OAuth configs
googleClientId = os.getenv("googleClientId", "")
googleClientSecret = os.getenv("googleClientSecret", "")
googleRedirectUri = os.getenv("googleRedirectUri", "http://localhost:8000/api/google/callback")

# System paths
baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dynamicToolsDir = os.path.join(baseDir, "dynamicTools")
os.makedirs(dynamicToolsDir, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
kernelLogger = logging.getLogger("AGNUX-KERNEL")

# AI telemetry stats tracked globally
aiStats = {
    "provider": iaProvider,
    "model": agnuxActiveModel,
    "status": "Online",
    "tokensPrompt": 0,
    "tokensResponse": 0,
    "totalTokens": 0,
    "lastErrorMessage": ""
}
