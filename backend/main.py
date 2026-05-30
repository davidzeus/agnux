from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import logger
from core.memory import inicializar_qdrant_colecciones

from api.routes import auth, intent

app = FastAPI(title="AGNUX OS Core API", version="2.0.0", redirect_slashes=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar colecciones de BD al arrancar
@app.on_event("startup")
async def inicializar_sistema():
    await inicializar_qdrant_colecciones()

# Registrar Rutas
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(intent.router, prefix="/api", tags=["System Intents"])
