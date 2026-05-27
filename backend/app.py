# app.py
import os
import sys
import logging
from datetime import datetime

# Parche estricto de rutas para subprocesos de Linux/Uvicorn
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Configuración de los Logs en la consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AGNUX_API")

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent_core import agnux_agent, recargar_herramientas_dinamicas

app = FastAPI(
    title="AGNUX Core Inmutable Engine",
    description="Motor de orquestación agéntica y lógica de bajo nivel para AGNUX OS.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agnux_state = {
    "usuario_activo": "user_cristian",
    "db_vectorial_actual": "./.agnux_storage",
    "actualizacion_pendiente": False
}

class SystemWindowManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def emitir_evento_sistema(self, evento: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(evento)
            except Exception:
                pass

window_manager = SystemWindowManager()

class TaskbarPrompt(BaseModel):
    prompt: str

@app.post("/api/system/intent")
async def procesar_intencion_global(payload: TaskbarPrompt):
    logger.info(f"📥 SOLICITUD RECIBIDA -> Prompt: '{payload.prompt}'")
    
    logger.info("🔄 Escaneando y recargando herramientas dinámicas...")
    recargar_herramientas_dinamicas()
    
    logger.info("🧠 Envíando prompt al agente de Agno (Ollama CPU). Esto puede demorar...")
    inicio_ia = datetime.now()
    
    loop = asyncio.get_event_loop()
    try:
        respuesta_agente = await loop.run_in_executor(None, agnux_agent.run, payload.prompt)
        tiempo_total = (datetime.now() - inicio_ia).total_seconds()
        
        logger.info(f"✅ IA RESPONDIÓ exitosamente en {tiempo_total:.2f} segundos.")
        return {
            "status": "success",
            "user": agnux_state["usuario_activo"],
            "response": respuesta_agente.content
        }
    except Exception as e:
        logger.error(f"❌ Error durante el procesamiento de la IA: {str(e)}")
        return {"status": "error", "detail": str(e)}

@app.websocket("/ws/system-events")
async def system_events_endpoint(websocket: WebSocket):
    await window_manager.connect(websocket)
    logger.info("🔌 Cliente WebSocket conectado al canal de eventos del sistema.")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        window_manager.disconnect(websocket)
        logger.info("🔌 Cliente WebSocket desconectado.")

@app.on_event("startup")
async def arrancar_servicios_nucleo():
    logger.info("🚀 NÚCLEO INDUSTRIAL DE AGNUX: Activo y securizado en Localhost.")