import json
import logging
from fastapi import WebSocket

kernelBusLogger = logging.getLogger("AGNUX-KERNEL-BUS")

class ConnectionManager:
    def __init__(self):
        # Dictionary to store active connections
        # Key: (terminalId, userId)
        # Value: WebSocket
        self.activeConnections: dict[tuple[str, str], WebSocket] = {}

    async def connect(self, websocket: WebSocket, terminalId: str, userId: str):
        await websocket.accept()
        self.activeConnections[(terminalId, userId)] = websocket
        kernelBusLogger.info(f"🟢 [KERNEL BUS] WebSocket conectado para Terminal '{terminalId}' (User: {userId})")

    def disconnect(self, terminalId: str, userId: str):
        if (terminalId, userId) in self.activeConnections:
            del self.activeConnections[(terminalId, userId)]
            kernelBusLogger.info(f"🔴 [KERNEL BUS] WebSocket desconectado para Terminal '{terminalId}' (User: {userId})")

    async def sendPersonalMessage(self, terminalId: str, userId: str, message: dict):
        websocket = self.activeConnections.get((terminalId, userId))
        if websocket:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                kernelBusLogger.error(f"❌ [KERNEL BUS] Error enviando mensaje por WS a ({terminalId}, {userId}): {e}")
                self.disconnect(terminalId, userId)
        else:
            kernelBusLogger.warning(f"⚠️ [KERNEL BUS] Intento de enviar mensaje a destinatario no conectado: ({terminalId}, {userId})")

manager = ConnectionManager()

async def notificarFrontendBus(terminalId: str, userId: str, mensaje: str, notificationType: str = "system"):
    """
    Función helper global para enviar una notificación push a la HyperIsland del frontend.
    """
    payload = {
        "type": "notification",
        "data": {
            "message": mensaje,
            "category": notificationType
        }
    }
    await manager.sendPersonalMessage(terminalId, userId, payload)
