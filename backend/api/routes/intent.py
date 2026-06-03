from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from core.kernelBus import manager
from schemas.models import TaskbarPrompt
from services.orchestrator import procesarGeneradorEventos
from api.routes.auth import googleAuthStatus

router = APIRouter()

@router.websocket("/system/notifications/ws/{terminalId}/{userId}")
async def websocketNotifications(websocket: WebSocket, terminalId: str, userId: str):
    await manager.connect(websocket, terminalId, userId)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(terminalId, userId)

@router.post("/system/intent")
async def procesarIntencionGlobal(payload: TaskbarPrompt):
    authStatus = await googleAuthStatus(payload.userId)
    isGoogleConnected = authStatus["connected"]
    
    return StreamingResponse(
        procesarGeneradorEventos(payload, isGoogleConnected), 
        media_type="text/event-stream"
    )
