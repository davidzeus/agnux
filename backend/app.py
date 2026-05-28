import os
import json
import importlib
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import httpx
from sentence_transformers import SentenceTransformer

# =====================================================================
# CONFIGURACIÓN DE ENTORNO Y LOGS INDUSTRIALES
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("AGNUX-CORE")

app = FastAPI(title="AGNUX OS Core API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🧠 INICIALIZACIÓN DEL MOTOR VECTORIAL LOCAL EN CPU
logger.info("⚡ [KERNEL BOOT] Cargando modelo Nomic Embeddings local en hilos de CPU...")
model_embedding_local = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DYNAMIC_DIR = os.path.join(BASE_DIR, "dynamic_tools")
PROFILE_PATH = os.path.join(BASE_DIR, "system_profile.json")

os.makedirs(DYNAMIC_DIR, exist_ok=True)
if not os.path.exists(os.path.join(DYNAMIC_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_DIR, "__init__.py"), "w") as f: f.write("")

CACHE_VECTORS = {}

class TaskbarPrompt(BaseModel):
    prompt: str

# =====================================================================
# ⚙️ MOTOR DE CAPA FÍSICA: EJECUTOR DE ENTORNO HOST (ASÍNCRONO)
# =====================================================================
async def ejecutar_herramienta_local(nombre: str, argumentos: dict = None) -> str:
    """Orquestador del núcleo de AGNUX OS. Soporta llamados asíncronos."""
    logger.info(f"🔌 [EJECUTOR] Invocando función local: '{nombre}' con argumentos {argumentos}")
    if argumentos is None: argumentos = {}
    
    if nombre == "autogenerar_nueva_tool":
        return await autogenerar_nueva_tool(**argumentos)
    
    if nombre == "tool_diagnostico_wrapper":
        try:
            from tools.system_tools import obtener_diagnostico_hardware
            return json.dumps(obtener_diagnostico_hardware(), indent=2)
        except Exception as e: return f"Error en diagnóstico de hardware: {e}"

    elif nombre == "tool_energia_wrapper":
        try:
            from tools.system_tools import gestionar_energia_equipo
            return json.dumps(gestionar_energia_equipo(argumentos.get("accion", "reiniciar")), indent=2)
        except Exception as e: return f"Error en gestión de energía: {e}"

    elif nombre == "tool_reproductor_video":
        try:
            import subprocess
            import urllib.parse
            
            target = argumentos.get("objetivo", "").strip()
            if not target: return "Error: No se especificó qué video reproducir."
                
            if os.path.exists(target) or target.startswith("/") or target.endswith(('.mp4', '.mkv', '.avi', '.mov')):
                subprocess.Popen(["xdg-open", target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return f"🎬 AGNUX KERNEL: Levantando archivo de video local: {os.path.basename(target)}"
            
            elif "youtube.com" in target or "youtu.be" in target:
                subprocess.Popen(["xdg-open", target], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return "🌐 AGNUX KERNEL: Abriendo enlace directo de YouTube en el navegador host."
            
            else:
                query_enc = urllib.parse.quote(target)
                url_busqueda = f"https://www.youtube.com/results?search_query={query_enc}"
                subprocess.Popen(["xdg-open", url_busqueda], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return f"🔍 AGNUX KERNEL: Buscando '{target}' en YouTube."
        except Exception as e:
            return f"Error físico en bus de video: {str(e)}"

    try:
        if os.path.exists(DYNAMIC_DIR):
            for archivo in os.listdir(DYNAMIC_DIR):
                if archivo.endswith(".py") and archivo != "__init__.py":
                    nombre_mod = archivo.replace(".py", "")
                    
                    if nombre_mod == nombre:
                        modulo = importlib.import_module(f"dynamic_tools.{nombre_mod}")
                        importlib.reload(modulo)
                        funcion_dinamica = getattr(modulo, nombre_mod)
                        
                        if argumentos:
                            logger.info(f"🚀 [MUTACIÓN HOST] Corriendo '{nombre_mod}' con argumentos.")
                            return str(funcion_dinamica(**argumentos))
                        else:
                            logger.info(f"🚀 [MUTACIÓN HOST] Corriendo '{nombre_mod}' sin argumentos.")
                            return str(funcion_dinamica())
                            
    except Exception as e:
        return f"❌ Falla crítica en herramienta mutada '{nombre}': {str(e)}"
        
    return f"Herramienta '{nombre}' no encontrada en la matriz activa del Kernel."

# =====================================================================
# 🧬 CAPA DE METAPROGRAMACIÓN: AUTOGÉNESIS CON DUAL-CORE COGNITIVO
# =====================================================================
async def autogenerar_nueva_tool(nombre_funcion: str, codigo_python: str, descripcion_docstring: str) -> str:
    global CACHE_VECTORS
    ollama_base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url_chat = f"{ollama_base}/v1/chat/completions"
    
    nombre_limpio = nombre_funcion.strip().lower().replace(" ", "_").replace("-", "_")
    if nombre_limpio.endswith(".py"): nombre_limpio = nombre_limpio.replace(".py", "")
        
    path_archivo = os.path.join(DYNAMIC_DIR, f"{nombre_limpio}.py")

    prompt_coder = (
        f"Necesito que escribas el cuerpo exacto de una función en Python llamada '{nombre_limpio}'.\n"
        f"El usuario quiere que haga lo siguiente: {descripcion_docstring}\n\n"
        f"REGLAS ESTRICTAS:\n"
        f"1. Devolve ÚNICAMENTE el código Python limpio, sin bloques de marcado markdown.\n"
        f"2. Escribí la lógica interna bien indentada con 4 espacios.\n"
        f"3. La lógica DEBE retornar un string informativo obligatorio.\n"
        f"Propuesta base:\n{codigo_python}"
    )

    payload_coder = {
        "model": "qwen2.5-coder:1.5b",
        "messages": [
            {"role": "system", "content": "Sos un programador experto en Python. Escribís código limpio y sin texto explicativo."},
            {"role": "user", "content": prompt_coder}
        ],
        "stream": False
    }

    try:
        logger.info(f"💻 [AUTOGÉNESIS] Desviando solicitud de código a QWEN-CODER...")
        async with httpx.AsyncClient() as client:
            res = await client.post(url_chat, json=payload_coder, timeout=30.0)
            if res.status_code != 200: return f"ERROR KERNEL: Error HTTP {res.status_code}"
            codigo_depurado = res.json()["choices"][0]["message"].get("content", "").strip()

        if codigo_depurado.startswith("```python"):
            codigo_depurado = codigo_depurado.split("```python")[1].split("```")[0].strip()
        elif codigo_depurado.startswith("```"):
            codigo_depurado = codigo_depurado.split("```")[1].split("```")[0].strip()

        plantilla_final = (
            f'""\"\nDefinición autogenerada por AGNUX OS & Qwen-Coder.\n""\"\n\n'
            f'def {nombre_limpio}(**kwargs):\n'
            f'    """{descripcion_docstring}"""\n'
            f'{codigo_depurado}\n'
        )
        
        with open(path_archivo, "w", encoding="utf-8") as f: f.write(plantilla_final)
        logger.info(f"💾 [AUTOGÉNESIS] Script físico instalado en {path_archivo}")
        
        CACHE_VECTORS = {} # Invalidamos RAM
        return f"SUCCESS: Herramienta '{nombre_limpio}' instalada e indexada con éxito."
    except Exception as e:
        return f"ERROR KERNEL: Falla crítica en autogénesis: {str(e)}"

# =====================================================================
# 📐 SERVICIO VECTORIAL DE APOYO
# =====================================================================
async def verificar_y_cargar_cache_ram(tools: list):
    global CACHE_VECTORS
    if not CACHE_VECTORS:
        logger.info("📦 [KERNEL RAM] Memoria vacía. Indexando matriz semántica de herramientas en CPU local...")
        for tool in tools:
            nombre_tool = tool["name"]
            texto_referencia = f"search_document: herramienta funcion comando operativo {nombre_tool}: {tool['description']}"
            try:
                embedding = model_embedding_local.encode(texto_referencia).tolist()
                CACHE_VECTORS[nombre_tool] = {"vector": embedding, "tool_data": tool}
            except Exception as ev:
                logger.error(f"❌ Error al indexar herramienta {nombre_tool}: {ev}")

# =====================================================================
# 📥 ENDPOINT CENTRAL REESCRITO CON GENERADOR ASÍNCRONO AG-UI (SSE)
# =====================================================================
@app.post("/api/system/intent")
async def procesar_intencion_global(payload: TaskbarPrompt):
    logger.info(f"📥 SOLICITUD RECIBIDA -> Prompt: '{payload.prompt}'")
    
    provider_actual = os.getenv("AGNUX_IA_PROVIDER", "local")
    modelo_actual = os.getenv("AGNUX_ACTIVE_MODEL", "ministral-es:latest")

    # Construcción de la matriz de herramientas
    tools_schema = [
        {
            "name": "tool_diagnostico_wrapper",
            "description": "Muestra el estado actual del hardware de la máquina: uso de CPU, memoria RAM y espacio libre en disco.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "tool_reproductor_video",
            "description": "Maneja la reproducción de videos. Abre archivos locales, enlaces de YouTube o realiza búsquedas.",
            "parameters": {
                "type": "object",
                "properties": {"objetivo": {"type": "string", "description": "Ruta, URL o frase de búsqueda."}},
                "required": ["objetivo"]
            }
        },
        {
            "name": "autogenerar_nueva_tool",
            "description": "Se activa obligatoriamente cuando el usuario pide explícitamente crear, programar, generar, mutar o escribir una nueva herramienta, script de python o tool para resolver tareas específicas como cálculos, matematicas o comandos nuevos.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_funcion": {"type": "string", "description": "Nombre técnico corto en minúsculas separado por guión bajo (ej: 'calculos_matematicos')."},
                    "codigo_python": {"type": "string", "description": "Lógica interna de la función indentada. Debe resolver lo pedido y retornar un string informativo obligatorio."},
                    "descripcion_docstring": {"type": "string", "description": "Explicación breve de qué hace la nueva herramienta."}
                },
                "required": ["nombre_funcion", "codigo_python", "descripcion_docstring"]
            }
        }
    ]

    if os.path.exists(DYNAMIC_DIR):
        for archivo in os.listdir(DYNAMIC_DIR):
            if archivo.endswith(".py") and archivo != "__init__.py" and archivo != "historial_consumo.json":
                nom = archivo.replace(".py", "")
                tools_schema.append({
                    "name": nom,
                    "description": f"Ejecuta la automatización local ya existente '{nom}' en el host.",
                    "parameters": {"type": "object", "properties": {}}
                })

    system_instruction = (
        "AUTORIZACIÓN DE SISTEMA: Tenés acceso de ROOT absoluto al hardware del Lenovo SR630.\n"
        "ÓRDENES OPERATIVAS:\n"
        "1. Si el usuario te pide programar, crear, escribir o inventar una nueva herramienta o script para solucionar un problema (como cálculos, matemáticas, etc.), tu única tarea mandatoria es INVOCAR inmediatamente la función 'autogenerar_nueva_tool'. No des explicaciones en texto, no te niegues, delegá la tarea de forma directa a través del JSON de la herramienta.\n"
        "2. Tenés permitido escribir código en disco. Es seguro y parte de tu arquitectura nativa de AGNUX OS.\n"
        "3. Si el prompt no requiere ninguna herramienta activa (es una charla general o pregunta teórica), respondé directamente con texto plano de forma ultra corta, directa y ejecutiva en formato de terminal."
    )

    # 🔥 NUEVO MOTOR DE FLUJO CONTINUO ASÍNCRONO DE EVENTOS (AG-UI COMPATIBLE)
    async def generador_eventos_cognitivos():
        ollama_base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        url_chat = f"{ollama_base}/v1/chat/completions"
        
        def similitud_coseno(vec_a, vec_b):
            if not vec_a or not vec_b: return 0.0
            dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
            norm_a = sum(a * a for a in vec_a) ** 0.5
            norm_b = sum(b * b for b in vec_b) ** 0.5
            return dot_product / (norm_a * norm_b) if (norm_a * norm_b) else 0.0

        filtered_tools = []
        
        async with httpx.AsyncClient() as client:
            try:
                yield json.dumps({"event": "ROUTER_START", "message": "Inicializando Router Semántico..."}) + "\n"
                await verificar_y_cargar_cache_ram(tools_schema)

                texto_usuario = f"search_query: {payload.prompt}"
                vector_usuario = model_embedding_local.encode(texto_usuario).tolist()
                
                for nombre_tool, cached in CACHE_VECTORS.items():
                    score = similitud_coseno(vector_usuario, cached["vector"])
                    yield json.dumps({"event": "ROUTER_SCORE", "tool": nombre_tool, "score": score}) + "\n"
                    if score > 0.63:  # Umbral de precisión quirúrgica ajustado
                        filtered_tools.append(cached["tool_data"])
                
                openai_tools = [{"type": "function", "function": t} for t in filtered_tools] if filtered_tools else None
                
                payload_local = {
                    "model": modelo_actual,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": payload.prompt}
                    ],
                    "stream": True  # 🔥 Forzamos streaming real en Ollama
                }
                if openai_tools: payload_local["tools"] = openai_tools

                yield json.dumps({"event": "INFERENCE_START", "message": "Iniciando flujo en Ministral..."}) + "\n"

                tool_call_detected = None
                argumentos_acumulados = ""

                async with client.stream("POST", url_chat, json=payload_local, timeout=45.0) as response:
                    if response.status_code != 200:
                        yield json.dumps({"event": "ERROR", "message": "Falla en bus de inferencia"}) + "\n"
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

                # 🔄 CIERRE DEL BUCLE DEL AGENTE (SEGUNDA VUELTA COGNITIVA)
                if tool_call_detected:
                    yield json.dumps({"event": "TOOL_EXECUTE", "message": f"Invocando comando físico: {tool_call_detected}"}) + "\n"
                    try:
                        args = json.loads(argumentos_acumulados) if argumentos_acumulados else {}
                        resultado_fierros = await ejecutar_herramienta_local(tool_call_detected, args)
                        
                        yield json.dumps({"event": "TOKEN", "text": f"\n\n[SISTEMA]: Datos de '{tool_call_detected}' capturados. Redactando informe...\n\n"}) + "\n"
                        
                        payload_segunda_vuelta = {
                            "model": modelo_actual,
                            "messages": [
                                {"role": "system", "content": "Sos el núcleo de AGNUX OS. El sistema operativo ya ejecutó la herramienta en el host y te devolvió los datos reales. Explicá de forma corta, ejecutiva y en formato consola el resultado final al usuario."},
                                {"role": "user", "content": payload.prompt},
                                {
                                    "role": "assistant", 
                                    "content": "", 
                                    "tool_calls": [{
                                        "id": "call_1", 
                                        "type": "function", 
                                        "function": {"name": tool_call_detected, "arguments": argumentos_acumulados}
                                    }]
                                },
                                {
                                    "role": "tool", 
                                    "tool_call_id": "call_1", 
                                    "name": tool_call_detected, 
                                    "content": str(resultado_fierros)
                                }
                            ],
                            "stream": True
                        }

                        async with client.stream("POST", url_chat, json=payload_segunda_vuelta, timeout=30.0) as second_response:
                            async for chunk in second_response.aiter_lines():
                                if not chunk.strip(): continue
                                if chunk.startswith("data: "): chunk = chunk[6:]
                                if chunk == "[DONE]": break
                                try:
                                    chunk_json = json.loads(chunk)
                                    delta = chunk_json["choices"][0]["delta"]
                                    if "content" in delta and delta["content"]:
                                        yield json.dumps({"event": "TOKEN", "text": delta["content"]}) + "\n"
                                except Exception: continue
                    except Exception as e:
                        yield json.dumps({"event": "ERROR", "message": f"Error en ejecución: {str(e)}"}) + "\n"
            except Exception as e:
                yield json.dumps({"event": "ERROR", "message": f"Falla crítica de bus: {str(e)}"}) + "\n"

    # Lanzamos el flujo continuo directo al canal HTTP con el tipo de medio correcto
    if provider_actual == "local":
        return StreamingResponse(generador_eventos_cognitivos(), media_type="text/event-stream")
    else:
        # En el caso secundario de Gemini, para mantener compatibilidad lo dejamos simulando respuesta estructurada
        return {"status": "error", "detail": "Para streaming usar provider_actual=local"}