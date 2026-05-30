import os
import json
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from qdrant_client.models import PointStruct

from core.config import logger, BASE_DIR
from core.memory import (
    qdrant_client, COLECCION_FACIAL, CACHE_VECTORS, TERMINAL_SESSIONS, 
    TEMPORARY_FACE_VECTORS, simular_vector_rostro
)
from schemas.models import LinkTerminalPayload, EnrolmentPayload

router = APIRouter()

@router.get("/theme/{user_id}")
async def obtener_tema_usuario(user_id: str):
    theme_path = os.path.join(BASE_DIR, "theme_profiles", f"{user_id}.css")
    if os.path.exists(theme_path):
        return FileResponse(theme_path, media_type="text/css")
    return {"status": "default_theme"}

@router.get("/auth/terminal-stream/{terminal_id}")
async def terminal_stream(terminal_id: str):
    TERMINAL_SESSIONS[terminal_id] = {"status": "pending", "user_id": None}
    logger.info(f"📡 [TERMINAL] Sesión abierta y esperando autenticación remota para: {terminal_id}")
    
    async def sse_bypass():
        try:
            while True:
                estado = TERMINAL_SESSIONS.get(terminal_id)
                if estado and estado.get("status") == "approved":
                    userid = estado.get("user-id") or estado.get("user_id")
                    logger.info(f"✅ [TERMINAL] Aprobación detectada. Liberando terminal para: {userid}")
                    yield f"event: AUTH-SUCCESS\ndata: {json.dumps({'userId': userid})}\n\n"
                    await asyncio.sleep(1.5)
                    break
                
                yield f"event: HEARTBEAT\ndata: {json.dumps({'status': 'keep-alive'})}\n\n"
                await asyncio.sleep(1.0)
        finally:
            TERMINAL_SESSIONS.pop(terminal_id, None)
            
    return StreamingResponse(sse_bypass(), media_type="text/event-stream")

@router.get("/auth/cloudflare/verify")
async def verify_cloudflare_auth(request: Request):
    # Cloudflare Access inyecta esta cabecera si el usuario pasó la barrera
    cf_email = request.headers.get("Cf-Access-Authenticated-User-Email")
    logger.info(f"DEBUG: Headers recibidos: {dict(request.headers)}")
    
    # [MODO DEV] Si estás desarrollando en local sin túnel, simular al admin
    if not cf_email and request.client.host in ("127.0.0.1", "::1", "localhost"):
        cf_email = "dev.local@agnux.net.ar"
        
    if not cf_email:
        logger.warn(f"⚠️ [CLOUDFLARE] Intento de acceso sin cabeceras. Cabeceras recibidas: {request.headers}")
        return {"status": "unauthenticated"}
        
    # Limpiamos el correo: 
    prefijo = cf_email.split("@")[0].lower()
    prefijo_limpio = prefijo.replace("_", "-").replace(".", "-")
    id_red = f"user-{prefijo_limpio}"
    
    # Aprovisionamiento en RAM al vuelo
    if id_red not in CACHE_VECTORS["usuarios"]:
        CACHE_VECTORS["usuarios"][id_red] = {}
        logger.info(f"🗂️ [RAM KERNEL] Slot privado creado al vuelo para: {id_red}")
        
    logger.info(f"✅ [CLOUDFLARE AUTH] Sesión inyectada con éxito para: {id_red} ({cf_email})")
    
    return {
        "status": "authenticated", 
        "user_id": id_red,
        "email": cf_email,
        "role": "admin"
    }

@router.post("/auth/facial-login")
@router.post("/auth/facial-login/")
async def facial_login(file: UploadFile = File(...)):
    try:
        contenido = await file.read()
        vector_rostro = simular_vector_rostro()
        
        search_result = None
        try:
            search_result = await qdrant_client.query_points(
                collection_name=COLECCION_FACIAL,
                query=vector_rostro,
                limit=1
            )
        except Exception as db_err:
            logger.warn(f"⚠️ [KERNEL QDRANT] No se pudo leer el vector de Qdrant ({str(db_err)}). Continuando en modo local seguro.")
        
        if search_result and search_result.points and search_result.points[0].score > 0.85: 
            user_id = search_result.points[0].payload.get("user_id")
            return {"status": "authenticated", "user_id": user_id}
        else:
            enrolment_id = str(uuid.uuid4())
            TEMPORARY_FACE_VECTORS[enrolment_id] = vector_rostro
            logger.info(f"📸 [BIOMETRÍA] Rostro DESCONOCIDO detectado. Emisión de EnrolmentID: {enrolment_id}")
            return {"status": "unknown_face", "enrolment_id": enrolment_id}
            
    except Exception as e:
        logger.error(f"Falla en bus de biometría facial: {e}")
        raise HTTPException(status_code=500, detail="Fallo catastrófico en análisis biométrico")

@router.post("/auth/register-profile")
@router.post("/auth/register-profile/")
async def register_profile(payload: EnrolmentPayload):
    if payload.enrolment_id not in TEMPORARY_FACE_VECTORS:
        raise HTTPException(status_code=400, detail="Error de seguridad: ID de enrolamiento expirado o ficticio")
        
    vector_rostro = TEMPORARY_FACE_VECTORS[payload.enrolment_id]
    user_id_limpio = "user-" + payload.nombre_usuario.strip().lower().replace(" ", "-").replace("_", "-")
    
    punto_id = int(datetime.now().timestamp() * 1000)
    punto = PointStruct(
        id=punto_id,
        vector=vector_rostro,
        payload={"user_id": user_id_limpio, "nombre": payload.nombre_usuario}
    )
    
    try:
        await qdrant_client.upsert(
            collection_name=COLECCION_FACIAL,
            points=[punto]
        )
        
        if user_id_limpio not in CACHE_VECTORS["usuarios"]:
            CACHE_VECTORS["usuarios"][user_id_limpio] = {}
            
        del TEMPORARY_FACE_VECTORS[payload.enrolment_id]
        logger.info(f"👤 [IDENTITY KERNEL] Nuevo perfil creado y blindado en RAM/Qdrant: {user_id_limpio}")
        
        return {"status": "profile_created", "user_id": user_id_limpio}
    except Exception as e:
        logger.error(f"Falla en registro profundo: {e}")
        raise HTTPException(status_code=500, detail="Error transaccional en persistencia de Qdrant DB")

@router.get("/auth/google/status")
@router.get("/auth/google/status/")
async def google_auth_status(user_id: str = Query(None, description="El ID del usuario")):
    is_connected = bool(user_id and user_id.lower() != "guest")
    return {"connected": is_connected, "userId": user_id}
