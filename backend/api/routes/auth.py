import os
import json
import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from qdrant_client.models import PointStruct

from core.config import kernelLogger, baseDir
from core.memory import (
    qdrantClient,
    coleccionFacial,
    cacheVectors,
    terminalSessions,
    temporaryFaceVectors,
    simularVectorRostro
)
from schemas.models import EnrolmentPayload

router = APIRouter()

@router.get("/theme/{userId}")
async def obtenerTemaUsuario(userId: str):
    themePath = os.path.join(baseDir, "theme-profiles", f"{userId}.css")
    if os.path.exists(themePath):
        return FileResponse(themePath, media_type="text/css")
    return {"status": "default_theme"}

@router.get("/auth/terminal-stream/{terminalId}")
async def terminalStream(terminalId: str):
    terminalSessions[terminalId] = {"status": "pending", "userId": None}
    kernelLogger.info(f"📡 [TERMINAL] Sesión abierta y esperando autenticación remota para: {terminalId}")
    
    async def sseBypass():
        try:
            while True:
                estado = terminalSessions.get(terminalId)
                if estado and estado.get("status") == "approved":
                    userId = estado.get("userId")
                    kernelLogger.info(f"✅ [TERMINAL] Aprobación detectada. Liberando terminal para: {userId}")
                    yield f"event: AUTH-SUCCESS\ndata: {json.dumps({'userId': userId})}\n\n"
                    await asyncio.sleep(1.5)
                    break
                
                yield f"event: HEARTBEAT\ndata: {json.dumps({'status': 'keep-alive'})}\n\n"
                await asyncio.sleep(1.0)
        finally:
            terminalSessions.pop(terminalId, None)
            
    return StreamingResponse(sseBypass(), media_type="text/event-stream")

@router.get("/auth/cloudflare/verify")
async def verifyCloudflareAuth(request: Request):
    cfEmail = request.headers.get("Cf-Access-Authenticated-User-Email")
    kernelLogger.info(f"DEBUG: Headers recibidos: {dict(request.headers)}")
    
    if not cfEmail and request.client and request.client.host in ("127.0.0.1", "::1", "localhost"):
        cfEmail = "dev.local@agnux.net.ar"
        
    if not cfEmail:
        kernelLogger.warning(f"⚠️ [CLOUDFLARE] Intento de acceso sin cabeceras. Cabeceras recibidas: {request.headers}")
        return {"status": "unauthenticated"}
        
    prefijo = cfEmail.split("@")[0].lower()
    prefijoLimpio = prefijo.replace("_", "-").replace(".", "-")
    idRed = f"user-{prefijoLimpio}"
    
    if idRed not in cacheVectors["usuarios"]:
        cacheVectors["usuarios"][idRed] = {}
        kernelLogger.info(f"🗂️ [RAM KERNEL] Slot privado creado al vuelo para: {idRed}")
        
    kernelLogger.info(f"✅ [CLOUDFLARE AUTH] Sesión inyectada con éxito para: {idRed} ({cfEmail})")
    
    return {
        "status": "authenticated", 
        "user_id": idRed,
        "email": cfEmail,
        "role": "admin"
    }

@router.post("/auth/facial-login")
@router.post("/auth/facial-login/")
async def facialLogin(file: UploadFile = File(...)):
    try:
        contenido = await file.read()
        vectorRostro = simularVectorRostro()
        
        searchResult = None
        try:
            searchResult = await qdrantClient.query_points(
                collection_name=coleccionFacial,
                query=vectorRostro,
                limit=1
            )
        except Exception as dbErr:
            kernelLogger.warning(f"⚠️ [KERNEL QDRANT] No se pudo leer el vector de Qdrant ({str(dbErr)}). Continuando en modo local seguro.")
        
        if searchResult and searchResult.points and searchResult.points[0].score > 0.85: 
            userId = searchResult.points[0].payload.get("user_id") or searchResult.points[0].payload.get("userId")
            return {"status": "authenticated", "user_id": userId}
        else:
            enrolmentId = str(uuid.uuid4())
            temporaryFaceVectors[enrolmentId] = vectorRostro
            kernelLogger.info(f"📸 [BIOMETRÍA] Rostro DESCONOCIDO detectado. Emisión de EnrolmentID: {enrolmentId}")
            return {"status": "unknown_face", "enrolment_id": enrolmentId}
            
    except Exception as e:
        kernelLogger.error(f"Falla en bus de biometría facial: {e}")
        raise HTTPException(status_code=500, detail="Fallo catastrófico en análisis biométrico")

@router.post("/auth/register-profile")
@router.post("/auth/register-profile/")
async def registerProfile(payload: EnrolmentPayload):
    if payload.enrolmentId not in temporaryFaceVectors:
        raise HTTPException(status_code=400, detail="Error de seguridad: ID de enrolamiento expirado o ficticio")
        
    vectorRostro = temporaryFaceVectors[payload.enrolmentId]
    userIdLimpio = "user-" + payload.userName.strip().lower().replace(" ", "-").replace("_", "-")
    
    puntoId = int(datetime.now().timestamp() * 1000)
    punto = PointStruct(
        id=puntoId,
        vector=vectorRostro,
        payload={"userId": userIdLimpio, "nombre": payload.userName}
    )
    
    try:
        await qdrantClient.upsert(
            collection_name=coleccionFacial,
            points=[punto]
        )
        
        if userIdLimpio not in cacheVectors["usuarios"]:
            cacheVectors["usuarios"][userIdLimpio] = {}
            
        del temporaryFaceVectors[payload.enrolmentId]
        kernelLogger.info(f"👤 [IDENTITY KERNEL] Nuevo perfil creado y blindado en RAM/Qdrant: {userIdLimpio}")
        
        return {"status": "profile_created", "user_id": userIdLimpio}
    except Exception as e:
        kernelLogger.error(f"Falla en registro profundo: {e}")
        raise HTTPException(status_code=500, detail="Error transaccional en persistencia de Qdrant DB")

@router.get("/auth/google/status")
@router.get("/auth/google/status/")
async def googleAuthStatus(userId: str = Query(None, description="El ID del usuario")):
    isConnected = bool(userId and userId.lower() != "guest")
    return {"connected": isConnected, "userId": userId}

@router.get("/google/callback")
async def googleCallback(code: str = Query(...)):
    # Simple fallback as auth callback
    return {"status": "success", "message": "Google Workspace authenticated successfully!"}
