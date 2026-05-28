import os
import json
import uuid
import logging
import asyncio
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# =====================================================================
# 1. CONFIGURACIÓN INICIAL Y DEPENDENCIAS
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AGNUX-CORE")

QDRANT_HOST = os.getenv("QDRANT_HOST", "http://qdrant_db:6333")
qdrant_client = AsyncQdrantClient(url=QDRANT_HOST)

app = FastAPI(title="AGNUX OS Core API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DYNAMIC_DIR = os.path.join(BASE_DIR, "dynamic_tools")
os.makedirs(DYNAMIC_DIR, exist_ok=True)
if not os.path.exists(os.path.join(DYNAMIC_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_DIR, "__init__.py"), "w") as f: f.write("")

# Simulación de un modelo de embeddings de rostro local
# En un escenario real, esto se cargaría al arrancar.
def simular_vector_rostro() -> list[float]:
    import random
    return [random.uniform(-1.0, 1.0) for _ in range(128)]

def simular_vector_texto(texto: str) -> list[float]:
    # Placeholder: simula la extracción de embedding (768 dimensiones)
    import random
    return [random.uniform(-1.0, 1.0) for _ in range(768)]

# =====================================================================
# 2. ESTRUCTURAS DE DATOS (Pydantic Models)
# =====================================================================
class TaskbarPrompt(BaseModel):
    prompt: str
    user_id: str

class EnrolmentPayload(BaseModel):
    enrolment_id: str
    nombre_usuario: str

class LinkTerminalPayload(BaseModel):
    terminal_id: str
    user_id: str

# =====================================================================
# 3. GESTIÓN DE MEMORIA GLOBAL (RAM KERNEL)
# =====================================================================
CACHE_VECTORS = {
    "sistema": {},
    "usuarios": {}
}
OLLAMA_BUS_LOCK = asyncio.Lock()
TEMPORARY_FACE_VECTORS = {}
TERMINAL_SESSIONS = {}

COLECCION_FACIAL = "perfiles_faciales"
COLECCION_MEMORIA = "agnux_kernel_memory"

@app.on_event("startup")
async def inicializar_sistema():
    logger.info("⚡ [KERNEL BOOT] Inicializando servicios base...")
    try:
        collections_response = await qdrant_client.get_collections()
        collection_names = [col.name for col in collections_response.collections]
        
        if COLECCION_FACIAL not in collection_names:
            logger.info(f"🧠 [QDRANT] Creando colección '{COLECCION_FACIAL}' (128d, COSINE)...")
            await qdrant_client.create_collection(
                collection_name=COLECCION_FACIAL,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
            
        if COLECCION_MEMORIA not in collection_names:
            logger.info(f"🧠 [QDRANT] Creando colección '{COLECCION_MEMORIA}' (768d, COSINE)...")
            await qdrant_client.create_collection(
                collection_name=COLECCION_MEMORIA,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
    except Exception as e:
        logger.error(f"❌ [QDRANT] Falla al inicializar bus vectorial: {e}")

# =====================================================================
# FUNCIONES AUXILIARES FÍSICAS Y AUTOGÉNESIS
# =====================================================================
async def autogenerar_nueva_tool(nombre_funcion: str, codigo_python: str, descripcion_docstring: str) -> str:
    ollama_base = os.getenv("OLLAMA_HOST", "http://10.10.0.48:11434").rstrip("/")
    url_chat = f"{ollama_base}/v1/chat/completions"
    
    nombre_limpio = nombre_funcion.strip().lower().replace(" ", "_").replace("-", "_")
    if nombre_limpio.endswith(".py"): nombre_limpio = nombre_limpio.replace(".py", "")
        
    path_archivo = os.path.join(DYNAMIC_DIR, f"{nombre_limpio}.py")

    prompt_coder = (
        f"Escribe el cuerpo de la función Python '{nombre_limpio}'.\n"
        f"Objetivo: {descripcion_docstring}\n\n"
        f"Retorna SOLO el código Python, sin markdown.\n"
    )

    payload_coder = {
        "model": "qwen2.5-coder:1.5b",
        "messages": [
            {"role": "system", "content": "Sos un experto Python. Código limpio. Sin markdown."},
            {"role": "user", "content": prompt_coder}
        ],
        "stream": False
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url_chat, json=payload_coder, timeout=30.0)
            if res.status_code != 200: return f"ERROR KERNEL: {res.status_code}"
            codigo_depurado = res.json()["choices"][0]["message"].get("content", "").strip()

        if codigo_depurado.startswith("```"):
            codigo_depurado = codigo_depurado.split("```")[1].replace("python", "", 1).strip()

        plantilla_final = (
            f'""\"\nAuto-generated by AGNUX OS.\n""\"\n\n'
            f'def {nombre_limpio}(**kwargs):\n'
            f'    """{descripcion_docstring}"""\n'
            f'{codigo_depurado}\n'
        )
        
        with open(path_archivo, "w", encoding="utf-8") as f: f.write(plantilla_final)
        logger.info(f"💾 [AUTOGÉNESIS] Tool instalada: {path_archivo}")
        
        return f"SUCCESS: '{nombre_limpio}' instalada con éxito."
    except Exception as e:
        return f"ERROR KERNEL: Falla crítica en autogénesis: {e}"

async def ejecutar_herramienta_local(nombre: str, argumentos: dict = None) -> str:
    logger.info(f"🔌 [EJECUTOR] Invocando: '{nombre}'")
    if argumentos is None: argumentos = {}
    
    if nombre == "autogenerar_nueva_tool":
        return await autogenerar_nueva_tool(**argumentos)
        
    try:
        if os.path.exists(DYNAMIC_DIR):
            import importlib
            for archivo in os.listdir(DYNAMIC_DIR):
                if archivo == f"{nombre}.py":
                    modulo = importlib.import_module(f"dynamic_tools.{nombre}")
                    importlib.reload(modulo)
                    funcion_dinamica = getattr(modulo, nombre)
                    resultado = funcion_dinamica(**argumentos) if argumentos else funcion_dinamica()
                    return str(resultado)
    except Exception as e:
        return f"❌ Falla en herramienta '{nombre}': {e}"
        
    return f"Herramienta '{nombre}' no encontrada."

# =====================================================================
# 4. ENDPOINT CORE DE INTENCIONES CON STREAMING AG-UI
# =====================================================================
@app.post("/api/system/intent")
async def procesar_intencion_global(payload: TaskbarPrompt):
    async def generador_eventos():
        if OLLAMA_BUS_LOCK.locked():
            yield json.dumps({"event": "QUEUE_WAIT", "message": "Servidor ocupado. Solicitud en cola de espera en el Kernel..."}) + "\n"
            
        async with OLLAMA_BUS_LOCK:
            ollama_host = os.getenv("OLLAMA_HOST", "http://10.10.0.48:11434").rstrip("/")
            url_chat = f"{ollama_host}/v1/chat/completions"
            
            yield json.dumps({"event": "ROUTER_START", "message": "Inicializando Router Semántico..."}) + "\n"
            
            # Fusión de tools
            tools_disponibles = {**CACHE_VECTORS["sistema"], **CACHE_VECTORS["usuarios"].get(payload.user_id, {})}
            
            # TODO: Simulación de vector de usuario y coseno. En entorno real usar sentence_transformers real
            vector_usuario = simular_vector_texto(payload.prompt)
            
            filtered_tools = []
            
            # Router de herramientas
            for nombre_tool, data in tools_disponibles.items():
                # placeholder score
                score = 0.8 # En la práctica sería: similitud_coseno(vector_usuario, data["vector"])
                yield json.dumps({"event": "ROUTER_SCORE", "tool": nombre_tool, "score": score}) + "\n"
                if score > 0.42:
                    filtered_tools.append(data["schema"])
                    
            # Inyección base de herramientas si no hay en cache
            if not filtered_tools:
                filtered_tools.append({
                    "name": "autogenerar_nueva_tool",
                    "description": "Se activa para programar una nueva herramienta",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "nombre_funcion": {"type": "string"},
                            "codigo_python": {"type": "string"},
                            "descripcion_docstring": {"type": "string"}
                        },
                        "required": ["nombre_funcion", "codigo_python", "descripcion_docstring"]
                    }
                })

            openai_tools = [{"type": "function", "function": t} for t in filtered_tools] if filtered_tools else None
            
            payload_local = {
                "model": "ministral-es:latest",
                "messages": [
                    {"role": "system", "content": "Sos el kernel de AGNUX OS. Responde corto y ejecutivo."},
                    {"role": "user", "content": payload.prompt}
                ],
                "stream": True
            }
            if openai_tools: payload_local["tools"] = openai_tools
            
            tool_call_detected = None
            argumentos_acumulados = ""
            
            try:
                async with httpx.AsyncClient() as client:
                    async with client.stream("POST", url_chat, json=payload_local, timeout=60.0) as response:
                        if response.status_code != 200:
                            yield json.dumps({"event": "ERROR", "message": f"HTTP {response.status_code}"}) + "\n"
                            return
                            
                        async for chunk in response.aiter_lines():
                            if not chunk.strip(): continue
                            if chunk.startswith("data: "): chunk = chunk[6:]
                            if chunk == "[DONE]": break
                            
                            try:
                                chunk_json = json.loads(chunk)
                                delta = chunk_json["choices"][0]["delta"]
                                
                                if "tool_calls" in delta and delta["tool_calls"]:
                                    tc = delta["tool_calls"][0]
                                    if "function" in tc:
                                        if tc["function"].get("name"): tool_call_detected = tc["function"]["name"]
                                        if tc["function"].get("arguments"): argumentos_acumulados += tc["function"]["arguments"]
                                elif "content" in delta and delta["content"]:
                                    yield json.dumps({"event": "TOKEN", "text": delta["content"]}) + "\n"
                            except Exception: continue
                            
            except Exception as e:
                yield json.dumps({"event": "ERROR", "message": f"Ollama Stream Falló: {e}"}) + "\n"
                return

            if tool_call_detected:
                yield json.dumps({"event": "TOOL_EXECUTE", "message": f"Invocando comando: {tool_call_detected}"}) + "\n"
                try:
                    args = json.loads(argumentos_acumulados) if argumentos_acumulados else {}
                    resultado_fierros = await ejecutar_herramienta_local(tool_call_detected, args)
                    
                    yield json.dumps({"event": "TOOL_RESULT", "data": resultado_fierros}) + "\n"
                    
                    # Promoción de tool
                    if tool_call_detected == "autogenerar_nueva_tool" and args.get("nombre_funcion", "").startswith("global_"):
                        nombre_func = args["nombre_funcion"]
                        CACHE_VECTORS["sistema"][nombre_func] = {
                            "vector": simular_vector_texto(args.get("descripcion_docstring", "")),
                            "schema": {
                                "name": nombre_func,
                                "description": args.get("descripcion_docstring", ""),
                                "parameters": {"type": "object", "properties": {}}
                            }
                        }
                        logger.info(f"🌐 [RAM KERNEL] Herramienta '{nombre_func}' promovida a GLOBAL.")
                        
                except Exception as e:
                    yield json.dumps({"event": "ERROR", "message": f"Falla en tool: {e}"}) + "\n"

    return StreamingResponse(generador_eventos(), media_type="text/event-stream")

# =====================================================================
# 5. CONTROL DE ACCESO BIOMÉTRICO
# =====================================================================
@app.post("/api/auth/facial-login")
async def facial_login(file: UploadFile = File(...)):
    try:
        contenido = await file.read()
        # Simula extracción geométrica a partir de imagen
        vector_rostro = simular_vector_rostro()
        
        search_result = await qdrant_client.search(
            collection_name=COLECCION_FACIAL,
            query_vector=vector_rostro,
            limit=1
        )
        
        if search_result and search_result[0].score > 0.85: # Umbral de similitud
            user_id = search_result[0].payload.get("user_id")
            return {"status": "authenticated", "user_id": user_id}
        else:
            enrolment_id = str(uuid.uuid4())
            TEMPORARY_FACE_VECTORS[enrolment_id] = vector_rostro
            return {"status": "unknown_face", "enrolment_id": enrolment_id}
            
    except Exception as e:
        logger.error(f"Falla en biometría: {e}")
        raise HTTPException(status_code=500, detail="Error biométrico")

@app.post("/api/auth/register-profile")
async def register_profile(payload: EnrolmentPayload):
    if payload.enrolment_id not in TEMPORARY_FACE_VECTORS:
        raise HTTPException(status_code=400, detail="Enrolment ID expirado o inválido")
        
    vector_rostro = TEMPORARY_FACE_VECTORS[payload.enrolment_id]
    user_id_limpio = payload.nombre_usuario.strip().lower().replace(" ", "_")
    
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
        
        # Inicializar slot en RAM
        if user_id_limpio not in CACHE_VECTORS["usuarios"]:
            CACHE_VECTORS["usuarios"][user_id_limpio] = {}
            
        del TEMPORARY_FACE_VECTORS[payload.enrolment_id]
        logger.info(f"👤 [IDENTITY] Nuevo perfil registrado: {user_id_limpio}")
        
        return {"status": "profile_created", "user_id": user_id_limpio}
    except Exception as e:
        logger.error(f"Falla al registrar perfil: {e}")
        raise HTTPException(status_code=500, detail="Error en Qdrant DB")

# =====================================================================
# 6. PUENTE DE BYPASS BIOMÉTRICO REMOTO
# =====================================================================
@app.get("/api/auth/terminal-stream")
async def terminal_stream(terminal_id: str):
    TERMINAL_SESSIONS[terminal_id] = "pending"
    
    async def sse_bypass():
        try:
            while True:
                estado = TERMINAL_SESSIONS.get(terminal_id)
                if estado and estado.startswith("approved:"):
                    user_id = estado.split(":")[1]
                    yield f"data: {json.dumps({'event': 'AUTH_SUCCESS', 'user_id': user_id})}\n\n"
                    break
                
                yield f"data: {json.dumps({'event': 'HEARTBEAT'})}\n\n"
                await asyncio.sleep(1.0)
        finally:
            TERMINAL_SESSIONS.pop(terminal_id, None)
            
    return StreamingResponse(sse_bypass(), media_type="text/event-stream")

@app.post("/api/auth/terminal-authorize")
async def terminal_authorize(payload: LinkTerminalPayload):
    if payload.terminal_id in TERMINAL_SESSIONS:
        TERMINAL_SESSIONS[payload.terminal_id] = f"approved:{payload.user_id}"
        logger.info(f"🔓 [BYPASS] Terminal {payload.terminal_id} desbloqueada remotamente por {payload.user_id}")
        return {"status": "success"}
    else:
        raise HTTPException(status_code=404, detail="Terminal no encontrada o inactiva")