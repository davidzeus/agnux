from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import kernelLogger
from core.memory import inicializarQdrantColecciones
from core.database import inicializarBaseDatos

from api.routes import auth, intent, system

@asynccontextmanager
async def lifespan(app: FastAPI):
    kernelLogger.info("🚀 [BOOT] Iniciando Kernel de AGNUX OS v2.0...")
    # Initialize SQLite database
    try:
        inicializarBaseDatos()
    except Exception as e:
        kernelLogger.error(f"❌ Error al inicializar SQLite: {e}")
        
    # Initialize Qdrant vectors
    try:
        await inicializarQdrantColecciones()
    except Exception as e:
        kernelLogger.error(f"❌ Error al inicializar Qdrant: {e}")
        
    yield
    kernelLogger.info("🔌 [SHUTDOWN] Cerrando Kernel de AGNUX OS...")

app = FastAPI(
    title="AGNUX OS Core API",
    version="2.0.0",
    redirect_slashes=True,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(intent.router, prefix="/api", tags=["System Intents"])
app.include_router(system.router, prefix="/api/system", tags=["System Status"])
