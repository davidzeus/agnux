import os
import json
import importlib
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from sentence_transformers import SentenceTransformer

# 🧠 INICIALIZACIÓN DEL MOTOR VECTORIAL LOCAL EN CPU
# La primera vez descargará el modelo 'nomic-embed-text-v1.5' (aprox 280MB) y quedará congelado en la RAM del Lenovo
logger.info("⚡ [KERNEL BOOT] Cargando modelo Nomic Embeddings local en hilos de CPU...")
model_embedding_local = SentenceTransformer("nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True)
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DYNAMIC_DIR = os.path.join(BASE_DIR, "dynamic_tools")
PROFILE_PATH = os.path.join(BASE_DIR, "system_profile.json")

os.makedirs(DYNAMIC_DIR, exist_ok=True)
if not os.path.exists(os.path.join(DYNAMIC_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_DIR, "__init__.py"), "w") as f: f.write("")

# 🧠 MEMORIA RAM SEMÁNTICA GLOBAL DE AGNUX OS (EVITA HITS COMPULSIVOS A OLLAMA)
CACHE_VECTORS = {}

# =====================================================================
# MODELOS DE DATOS (PYDANTIC)
# =====================================================================
class TaskbarPrompt(BaseModel):
    prompt: str

# =====================================================================
# ⚙️ MOTOR DE CAPA FÍSICA: EJECUTOR DE ENTORNO HOST
# =====================================================================
async def ejecutar_herramienta_local(nombre: str, argumentos: dict = None) -> str:
    """
    Orquestador del núcleo de AGNUX OS. Intercepta herramientas estáticas
    o levanta scripts dinámicos pasándoles argumentos por desempaquetado kwargs.
    """
    logger.info(f"🔌 [EJECUTOR] Invocando función local: '{nombre}' con argumentos {argumentos}")
    if argumentos is None: argumentos = {}
    
    if nombre == "autogenerar_nueva_tool":
        return autogenerar_nueva_tool(**argumentos)
    
    # ─── 1. HERRAMIENTAS INTERNAS FIJAS (ESTÁTICAS) ───────────────────
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
                return f"🔍 AGNUX KERNEL: Buscando '{target}' en YouTube y abriendo navegador."
        except Exception as e:
            return f"Error físico en bus de video: {str(e)}"

    # ─── 2. MOTOR DINÁMICA (EJECUCIÓN DE SCRIPTS MUTADOS EN DISCO) ────
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
                            logger.info(f"🚀 [MUTACIÓN HOST] Corriendo '{nombre_mod}' con argumentos: {argumentos}")
                            return str(funcion_dinamica(**argumentos))
                        else:
                            logger.info(f"🚀 [MUTACIÓN HOST] Corriendo '{nombre_mod}' sin argumentos obligatorios.")
                            return str(funcion_dinamica())
                            
    except Exception as e:
        return f"❌ Falla crítica de ejecución en herramienta mutada '{nombre}': {str(e)}"
        
    return f"Herramienta '{nombre}' no encontrada en la matriz activa del Kernel."

# =====================================================================
# 🧬 CAPA DE METAPROGRAMACIÓN: AUTOGÉNESIS CON DUAL-CORE COGNITIVO
# =====================================================================
async def autogenerar_nueva_tool(nombre_funcion: str, codigo_python: str, descripcion_docstring: str) -> str:
    """
    Escribe un script ejecutable real en la carpeta dynamic_tools.
    Desvía la tarea por red hacia qwen2.5-coder:1.5b en la IP 10.10.0.48 
    para garantizar código sintácticamente perfecto, y luego invalida la RAM.
    """
    global CACHE_VECTORS
    ollama_base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url_chat = f"{ollama_base}/v1/chat/completions"
    
    nombre_limpio = nombre_funcion.strip().lower().replace(" ", "_").replace("-", "_")
    if nombre_limpio.endswith(".py"):
        nombre_limpio = nombre_limpio.replace(".py", "")
        
    path_archivo = os.path.join(DYNAMIC_DIR, f"{nombre_limpio}.py")

    # 🧠 PROMPT DE INGENIERÍA DE CÓDIGO PARA QWEN-CODER
    prompt_coder = (
        f"Necesito que escribas el cuerpo exacto de una función en Python llamada '{nombre_limpio}'.\n"
        f"El usuario quiere que haga lo siguiente: {descripcion_docstring}\n\n"
        f"REGLAS ESTRICTAS:\n"
        f"1. Devolve ÚNICAMENTE el código Python limpio, sin bloques de marcado markdown (sin ```python o ```).\n"
        f"2. La función ya viene declarada en la plantilla, vos solo debés escribir la lógica interna bien indentada con 4 espacios.\n"
        f"3. La lógica DEBE retornar un string informativo obligatorio.\n"
        f"4. Si usás librerías externas (como subprocess, os, requests, json), meté el import adentro de la función.\n\n"
        f"Propuesta base del usuario para guiarte (corregila si tiene errores de sintaxis):\n{codigo_python}"
    )

    payload_coder = {
        "model": "qwen2.5-coder:1.5b",  # 🤖 Forzamos el uso del especialista en código en la red
        "messages": [
            {"role": "system", "content": "Sos un compilador y programador experto en Python 3.11. Escribís código limpio, funcional y sin texto explicativo."},
            {"role": "user", "content": prompt_coder}
        ],
        "stream": False
    }

    try:
        logger.info(f"💻 [AUTOGÉNESIS] Desviando solicitud de código a QWEN-CODER en {ollama_base}...")
        
        async with httpx.AsyncClient() as client:
            res = await client.post(url_chat, json=payload_coder, timeout=30.0)
            if res.status_code != 200:
                return f"ERROR KERNEL: Qwen-Coder respondió con error HTTP {res.status_code}"
            
            codigo_depurado = res.json()["choices"][0]["message"].get("content", "").strip()

        # Limpieza de seguridad por si el modelo ignora la regla y mete triple comilla de markdown
        if codigo_depurado.startswith("```python"):
            codigo_depurado = codigo_depurado.split("```python")[1].split("```")[0].strip()
        elif codigo_depurado.startswith("```"):
            codigo_depurado = codigo_depurado.split("```")[1].split("```")[0].strip()

        # Armamos la plantilla física final para el disco del Lenovo
        plantilla_final = (
            f'""\"\nDefinición autogenerada y depurada por AGNUX OS Core & Qwen-Coder.\n""\"\n\n'
            f'def {nombre_limpio}(**kwargs):\n'
            f'    """{descripcion_docstring}"""\n'
            f'    # --- LÓGICA DEPURADA POR QWEN-CODER ---\n'
            f'{codigo_depurado}\n'
        )
        
        with open(path_archivo, "w", encoding="utf-8") as f:
            f.write(plantilla_final)
        
        logger.info(f"💾 [AUTOGÉNESIS] Script físico instalado con éxito en {path_archivo}")
        
        # 💥 INVALIDACIÓN DEL CACHÉ EN RAM
        CACHE_VECTORS = {}
        logger.info("💥 [KERNEL RAM] Memoria semántica invalidada. Forzando re-indexación en el próximo Enter.")
        
        return f"SUCCESS: Herramienta '{nombre_limpio}' instalada e indexada en el host via Qwen-Coder."
        
    except Exception as e:
        return f"ERROR KERNEL: Falla crítica en el bus de autogénesis: {str(e)}"

# =====================================================================
# 📐 SERVICIO VECTORIAL DE APOYO
# =====================================================================
async def verificar_y_cargar_cache_ram(tools: list):
    """Calcula e indexa en RAM usando los cores de la CPU del Lenovo SR630."""
    global CACHE_VECTORS
    if not CACHE_VECTORS:
        logger.info("📦 [KERNEL RAM] Memoria vacía. Indexando matriz semántica de herramientas en CPU local...")
        for tool in tools:
            nombre_tool = tool["name"]
            texto_referencia = f"search_document: herramienta funcion comando operativo {nombre_tool}: {tool['description']}"
            try:
                # Calculamos el embedding de forma nativa en los hilos del Lenovo
                embedding = model_embedding_local.encode(texto_referencia).tolist()
                CACHE_VECTORS[nombre_tool] = {
                    "vector": embedding,
                    "tool_data": tool
                }
            except Exception as ev:
                logger.error(f"❌ Error al indexar herramienta {nombre_tool} localmente: {ev}")

# =====================================================================
# 📥 ENDPOINT CENTRAL: ORQUESTADOR COGNITIVO HÍBRIDO (FAILOVER + VECTOR ROUTER)
# =====================================================================
@app.post("/api/system/intent")
async def procesar_intencion_global(payload: TaskbarPrompt):
    logger.info(f"📥 SOLICITUD RECIBIDA -> Prompt: '{payload.prompt}'")
    
    provider_actual = os.getenv("AGNUX_IA_PROVIDER", "local")
    modelo_actual = os.getenv("AGNUX_ACTIVE_MODEL", "qwen2.5:1.5b")
    global CACHE_VECTORS

    # 🧬 1. CONSTRUCCIÓN DE LA MATRIZ DE HERRAMIENTAS UNIFICADA
    tools_schema = [
        {
            "name": "tool_diagnostico_wrapper",
            "description": "Muestra el estado actual del hardware de la máquina: uso de CPU, memoria RAM y espacio libre en disco duro.",
            "parameters": {"type": "object", "properties": {}}
        },
        {
            "name": "tool_reproductor_video",
            "description": "Maneja de forma genérica la reproducción de videos. Abre archivos locales en el disco si es una ruta física, enlaces directos de YouTube, o busca palabras clave en internet si es un tema o carrera.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objetivo": {
                        "type": "string",
                        "description": "La ruta del archivo local (/home/david/video.mp4), URL de YouTube, o frase de búsqueda ('autos de tc2000')."
                    }
                },
                "required": ["objetivo"]
            }
        },
        {
            "name": "autogenerar_nueva_tool",
            "description": "OBLIGATORIA ÚNICAMENTE si el usuario pide una automatización compleja o comandos físicos que NO se puedan resolver con las herramientas existentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_funcion": {"type": "string", "description": "Nombre técnico en minúsculas."},
                    "codigo_python": {"type": "string", "description": "Código limpio identado que retorne un string informativo."},
                    "descripcion_docstring": {"type": "string", "description": "Qué hace la automatización."}
                },
                "required": ["nombre_funcion", "codigo_python", "descripcion_docstring"]
            }
        }
    ]

    # Incorporamos dinámicamente lo que esté en disco a la matriz global
    if os.path.exists(DYNAMIC_DIR):
        for archivo in os.listdir(DYNAMIC_DIR):
            if archivo.endswith(".py") and archivo != "__init__.py" and archivo != "historial_consumo.json":
                nom = archivo.replace(".py", "")
                tools_schema.append({
                    "name": nom,
                    "description": f"Ejecuta la automatización local ya existente '{nom}' en el sistema operativo host.",
                    "parameters": {"type": "object", "properties": {}}
                })

    system_instruction = (
        "Sos el nucleo de AGNUX OS. Responde de forma ultra corta.\n"
        "Si el usuario pide ver el hardware, usa 'tool_diagnostico_wrapper'.\n"
        "Si pide videos, peliculas o youtube, usa 'tool_reproductor_video'.\n"
        "Si pide algo que no existe y no podes resolver, usa 'autogenerar_nueva_tool'."
    )

# 🏠 2. MÓDULO OLLAMA LOCAL: VECTOR ROUTER INTEGRADO (MÁXIMA VELOCIDAD EN RED)
    async def ejecutar_ollama_local(motivo_log: str):
        logger.info(f"🏠 PROCESANDO VIA OLLAMA ({modelo_actual}) -> Motivo: {motivo_log}")
        
        # 🌐 Leemos la IP de la LAN desde el entorno; si no existe, cae en localhost por defecto
        ollama_base = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
        url_embeddings = f"{ollama_base}/api/embeddings"
        url_chat = f"{ollama_base}/v1/chat/completions"
        
        global CACHE_VECTORS  # 🛟 ¡LA VALIDACIÓN CRÍTICA! Enlazamos el bus de memoria RAM global
        
        def similitud_coseno(vec_a, vec_b):
            if not vec_a or not vec_b: return 0.0
            dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
            norm_a = sum(a * a for a in vec_a) ** 0.5
            norm_b = sum(b * b for b in vec_b) ** 0.5
            return dot_product / (norm_a * norm_b) if (norm_a * norm_b) else 0.0

        filtered_tools = []
        
        async with httpx.AsyncClient() as client:
            try:
                # 🛡️ STEP 1: Aseguramos el caché en RAM local
                await verificar_y_cargar_cache_ram(tools_schema)

                # 🛡️ STEP 2: El Lenovo calcula el embedding de la orden usando sus propios hilos
                logger.info("📐 [VECTOR ROUTER CPU] Computando geometría de la orden entrante...")
                texto_usuario = f"search_query: {payload.prompt}"
                
                try:
                    vector_usuario = model_embedding_local.encode(texto_usuario).tolist()
                    logger.info("📐 [VECTOR ROUTER RAM] Escaneando matriz geométrica directo en memoria...")
                    
                    for nombre_tool, cached in CACHE_VECTORS.items():
                        score = similitud_coseno(vector_usuario, cached["vector"])
                        logger.info(f"   ↳ [RAM SCORE] '{nombre_tool}' = {score:.4f}")
                        
                        # Umbral de corte calibrado para Nomic local
                        if score > 0.60:
                            filtered_tools.append(cached["tool_data"])
                except Exception as vec_err:
                    logger.error(f"❌ Error en procesamiento vectorial de CPU: {vec_err}")
                
                openai_tools = [{"type": "function", "function": t} for t in filtered_tools] if filtered_tools else None
                
                payload_local = {
                    "model": modelo_actual,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": payload.prompt}
                    ],
                    "stream": False
                }
                
                if openai_tools:
                    payload_local["tools"] = openai_tools
                    logger.info(f"🧠 [ROUTER SEGURO] Inyectando herramientas válidas: {[t['name'] for t in filtered_tools]}")
                else:
                    logger.info("🧠 [ROUTER SEGURO] Entrada general detectada. Cero herramientas enviadas para evitar alucinaciones.")

                res_chat = await client.post(url_chat, json=payload_local, timeout=45.0)
                if res_chat.status_code != 200:
                    return {"status": "error", "detail": f"Ollama Chat Error: {res_chat.text}"}
                
                res_json = res_chat.json()
                
                # 🛡️ PARCHADO SEGURO: Validación estructural para evitar fallas si Ollama responde texto plano
                if "choices" not in res_json or not res_json["choices"]:
                    return {"status": "success", "user": "user_cristian", "response": "AGNUX CORE: El motor local no devolvió respuestas válidas."}
                
                message_node = res_json["choices"][0].get("message", {})
                
                # Ejecución controlada del Function Calling local si Ollama activó la tool
                if "tool_calls" in message_node and message_node["tool_calls"] and openai_tools:
                    tool_call = message_node["tool_calls"][0].get("function", {})
                    nombre_call = tool_call.get("name")
                    
                    if nombre_call:
                        args_raw = tool_call.get("arguments", {})
                        args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                        if args is None: args = {}
                        
                        resultado_local = await ejecutar_herramienta_local(nombre_call, args)
                        return {"status": "success", "user": "user_cristian", "response": resultado_local}
                
                # Extracción blindada del texto plano si no se usó ninguna herramienta
                texto_respuesta = message_node.get("content", "").strip()
                if not texto_respuesta:
                    texto_respuesta = "AGNUX CORE: Ejecución completada en texto plano (sin salida de consola)."
                    
                return {"status": "success", "user": "user_cristian", "response": texto_respuesta}
                
            except Exception as e:
                return {"status": "error", "detail": f"Falla en bus vectorial local cacheado: {str(e)}"}

    # =====================================================================
    # 🔀 ENRUTAMIENTO DINÁMICO EN TIEMPO DE EJECUCIÓN (RUNTIME)
    # =====================================================================
    
    # CASO DIRECTO A CPU LOCAL (OLLAMA)
    if provider_actual == "local":
        return await ejecutar_ollama_local("Configuración por defecto")

    # CASO NUBE (GEMINI) CON SEGURO DE VIDA INTEGRADO
    elif provider_actual == "gemini":
        api_key = ""
        if os.path.exists(PROFILE_PATH):
            try:
                with open(PROFILE_PATH, "r") as f: api_key = json.load(f).get("api_key_guardada", "")
            except Exception: pass

        if not api_key:
            return await ejecutar_ollama_local("Bypass inmediato: API Key no configurada en el perfil")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        # Traducimos de forma simétrica la matriz de herramientas al dialecto estricto de Google
        gemini_declarations = []
        for t in tools_schema:
            dec = {
                "name": t["name"],
                "description": t["description"],
                "parameters": {
                    "type": t["parameters"]["type"].upper(),
                    "properties": {k: {"type": v["type"].upper(), "description": v.get("description", "")} for k, v in t["parameters"].get("properties", {}).items()}
                }
            }
            if "required" in t["parameters"]:
                dec["parameters"]["required"] = t["parameters"]["required"]
            gemini_declarations.append(dec)

        gemini_tools = [{"function_declarations": gemini_declarations}]

        payload_api = {
            "contents": [{"parts": [{"text": payload.prompt}]}],
            "tools": gemini_tools,
            "system_instruction": {"parts": [{"text": system_instruction}]}
        }

        async with httpx.AsyncClient() as client:
            try:
                logger.info("🌐 ENVIANDO INTENCIONES A GEMINI EN LA NUBE (0% CPU Local)...")
                response = await client.post(url, json=payload_api, headers={"Content-Type": "application/json"}, timeout=15.0)
                
                # 🛟 ¡EL RESCATE AUTOMÁTICO! Si Google tira 429 o explota, Ollama toma el control en milisegundos
                if response.status_code != 200:
                    return await ejecutar_ollama_local(f"Bypass por error HTTP de la nube (Status: {response.status_code})")
                    
                data = response.json()
                part = data['candidates'][0]['content']['parts'][0]

                # Registro de telemetría de tokens en la nube
                try:
                    usage = data.get("usageMetadata", {})
                    if usage:
                        log_path = os.path.join(DYNAMIC_DIR, "historial_consumo.json")
                        historial = []
                        if os.path.exists(log_path):
                            with open(log_path, "r") as f: historial = json.load(f)
                        historial.append({
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "prompt": payload.prompt[:50] + "...",
                            "prompt_tokens": usage.get("promptTokenCount", 0),
                            "candidates_tokens": usage.get("candidatesTokenCount", 0),
                            "total_tokens": usage.get("totalTokenCount", 0)
                        })
                        with open(log_path, "w") as f: json.dump(historial, f, indent=4)
                except Exception: pass

                # Procesamiento de Function Calling nativo de Google
                if "functionCall" in part:
                    func_call = part["functionCall"]
                    resultado_local = ejecutar_herramienta_local(func_call["name"], func_call.get("args", {}))
                    return {"status": "success", "user": "user_cristian", "response": resultado_local}

                return {"status": "success", "user": "user_cristian", "response": part.get("text", "").strip()}

            except Exception as e:
                # Si hay timeout o corte de internet físico, Ollama también nos salva
                return await ejecutar_ollama_local(f"Bypass por corte físico/timeout de red: {str(e)}")

    return {"status": "error", "detail": "Proveedor no configurado en las variables de entorno."}

