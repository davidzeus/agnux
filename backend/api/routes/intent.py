from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from kernel_bus import manager
from schemas.models import TaskbarPrompt
from services.intent_orchestrator import procesar_generador_eventos
from api.routes.auth import google_auth_status

router = APIRouter()

@router.websocket("/system/notifications/ws/{terminal_id}/{user_id}")
async def websocket_notifications(websocket: WebSocket, terminal_id: str, user_id: str):
    await manager.connect(websocket, terminal_id, user_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(terminal_id, user_id)

@router.post("/system/intent")
async def procesar_intencion_global(payload: TaskbarPrompt):
    # Verificación de Token OAuth2 Preventiva
    auth_status = await google_auth_status(payload.user_id)
    is_google_connected = auth_status["connected"]
    
    return StreamingResponse(
        procesar_generador_eventos(payload, is_google_connected), 
        media_type="text/event-stream"
    )
