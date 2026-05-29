import json
import logging
from fastapi import WebSocket

logger = logging.getLogger("AGNUX-KERNEL-BUS")

class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections
        # Key: (terminal_id, user_id)
        # Value: WebSocket
        self.active_connections: dict[tuple[str, str], WebSocket] = {}

    async def connect(self, websocket: WebSocket, terminal_id: str, user_id: str):
        await websocket.accept()
        self.active_connections[(terminal_id, user_id)] = websocket
        logger.info(f"🟢 [KERNEL BUS] WebSocket conectado para Terminal '{terminal_id}' (User: {user_id})")

    def disconnect(self, terminal_id: str, user_id: str):
        if (terminal_id, user_id) in self.active_connections:
            del self.active_connections[(terminal_id, user_id)]
            logger.info(f"🔴 [KERNEL BUS] WebSocket desconectado para Terminal '{terminal_id}' (User: {user_id})")

    async def send_personal_message(self, terminal_id: str, user_id: str, message: dict):
        websocket = self.active_connections.get((terminal_id, user_id))
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"❌ [KERNEL BUS] Error enviando mensaje por WS a ({terminal_id}, {user_id}): {e}")
                self.disconnect(terminal_id, user_id)
        else:
            logger.warning(f"⚠️ [KERNEL BUS] Intento de enviar mensaje a destinatario no conectado: ({terminal_id}, {user_id})")

manager = ConnectionManager()

async def notificar_frontend(terminal_id: str, user_id: str, mensaje: str, notification_type: str = "system"):
    """
    Función helper global para enviar una notificación push a la HyperIsland del frontend.
    Puede ser importada y utilizada por cualquier herramienta autogenerada.
    """
    payload = {
        "type": "notification",
        "data": {
            "message": mensaje,
            "category": notification_type
        }
    }
    await manager.send_personal_message(terminal_id, user_id, payload)
