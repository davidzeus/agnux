# app.py
import os
import sys
import logging
import json
import httpx
import importlib
import asyncio
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =====================================================================
# 🛠️ CONFIGURACIÓN DE ENTORNO Y RUTAS INDUSTRIALES
# =====================================================================
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
logger = logging.getLogger("AGNUX_CORE")

PROFILE_PATH = os.path.join(base_dir, "system_profile.json")
DYNAMIC_DIR = os.path.join(base_dir, "dynamic_tools")
os.makedirs(DYNAMIC_DIR, exist_ok=True)

if not os.path.exists(os.path.join(DYNAMIC_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_DIR, "__init__.py"), "w") as f: f.write("")

app = FastAPI(title="AGNUX Engine", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class TaskbarPrompt(BaseModel):
    prompt: str

# =====================================================================
# 🧬 MATRIZ DE HERRAMIENTAS NATIVAS DE AGNUX (EJECUCIÓN LOCAL)
# =====================================================================
def autogenerar_nueva_tool(nombre_funcion: str, codigo_python: str, descripcion_docstring: str) -> str:
    logger.info(f"🛠️ [AUTOGÉNESIS] Creando nueva herramienta: '{nombre_funcion}'...")
    try:
        nombre_clean = nombre_funcion.strip().replace(" ", "_")
        nombre_archivo = f"{DYNAMIC_DIR}/{nombre_clean}.py"
        contenido_codigo = f'"""\nDefinición autogenerada por AGNUX OS Core.\n"""\n\ndef {nombre_clean}():\n    """{descripcion_docstring}"""\n{codigo_python}\n'
        with open(nombre_archivo, "w") as f: f.write(contenido_codigo)
        logger.info(f"💾 [AUTOGÉNESIS] Código escrito con éxito en {nombre_archivo}")
        return f"SUCCESS: Herramienta '{nombre_clean}' instalada en el host."
    except Exception as e:
        return f"ERROR en autogénesis: {str(e)}"

def ejecutar_herramienta_local(nombre: str, argumentos: dict = None) -> str:
    """Orquestador dinámico que ejecuta funciones estáticas o dinámicas en el host real."""
    logger.info(f"🔌 [EJECUTOR] Invocando función local: '{nombre}' con argumentos {argumentos}")
    if argumentos is None: argumentos = {}
    
    if nombre == "autogenerar_nueva_tool":
        return autogenerar_nueva_tool(**argumentos)
    
    # Intentar ejecutar wrappers estáticos mapeados
    try:
        from tools.system_tools import obtener_diagnostico_hardware, gestionar_energia_equipo
        from tools.multimedia_tools import ejecutar_musica_fondo, controlar_reproductor_global
        
        if nombre == "tool_diagnostico_wrapper":
            return json.dumps(obtener_diagnostico_hardware(), indent=2)
        elif nombre == "tool_energia_wrapper":
            return json.dumps(gestionar_energia_equipo(argumentos.get("accion", "reiniciar")), indent=2)
        elif nombre == "tool_musica_wrapper":
            return str(ejecutar_musica_fondo(argumentos.get("busqueda_o_url", "")))
        elif nombre == "tool_control_audio_wrapper":
            return str(controlar_reproductor_global(argumentos.get("accion", "pausa")))
    except Exception as e:
        logger.warning(f"No se pudo ejecutar la herramienta estática básica: {e}")

    # Buscar en herramientas dinámicas autogeneradas en el disco
    try:
        if os.path.exists(DYNAMIC_DIR):
            for archivo in os.listdir(DYNAMIC_DIR):
                if archivo.endswith(".py") and archivo != "__init__.py":
                    nombre_mod = archivo.replace(".py", "")
                    if nombre_mod == nombre:
                        modulo = importlib.import_module(f"dynamic_tools.{nombre_mod}")
                        importlib.reload(modulo)
                        funcion = getattr(modulo, nombre_mod)
                        return str(funcion())
    except Exception as e:
        return f"Error ejecutando herramienta dinámica '{nombre}': {str(e)}"
        
    return f"Herramienta '{nombre}' no encontrada en el Kernel."

# =====================================================================
# 📥 ENDPOINT: ORQUESTADOR COGNITIVO UNIFICADO Y SIMÉTRICO (NATIVO)
# =====================================================================
@app.post("/api/system/intent")
async def procesar_intencion_global(payload: TaskbarPrompt):
    logger.info(f"📥 SOLICITUD RECIBIDA -> Prompt: '{payload.prompt}'")
    
    provider_actual = os.getenv("AGNUX_IA_PROVIDER", "local")
    modelo_actual = os.getenv("AGNUX_ACTIVE_MODEL", "qwen2.5:1.5b")
    
    # 🧬 1. MATRIZ ÚNICA DE HERRAMIENTAS (Formato Estándar de Mercado)
    # Cualquier cambio acá impacta automáticamente en Ollama y en Gemini
    tools_schema = [
        {
            "name": "tool_diagnostico_wrapper",
            "description": "Muestra el estado actual del hardware de la máquina: uso de CPU, memoria RAM y espacio en disco duro.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "tool_reproductor_video",
            "description": "Maneja de forma genérica la reproducción de videos. Abre archivos locales en el disco si es una ruta física, enlaces directos de YouTube, o busca palabras clave en internet si es un tema o categoría.",
            "parameters": {
                "type": "object",
                "properties": {
                    "objetivo": {
                        "type": "string",
                        "description": "La ruta del archivo local (ej: /home/david/video.mp4), URL de YouTube, o frase de búsqueda (ej: 'autos de tc2000')."
                    }
                },
                "required": ["objetivo"]
            }
        },
        {
            "name": "autogenerar_nueva_tool",
            "description": "OBLIGATORIA ÚNICAMENTE si el usuario pide una automatización compleja que NO se pueda resolver con las herramientas existentes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_funcion": {"type": "string", "description": "Nombre técnico en minúsculas (ej: control_compresor)."},
                    "codigo_python": {"type": "string", "description": "Código limpio que retorne string."},
                    "descripcion_docstring": {"type": "string"}
                },
                "required": ["nombre_funcion", "codigo_python", "descripcion_docstring"]
            }
        }
    ]

    # Incorporamos al esquema dinámico las herramientas guardadas en el disco
    if os.path.exists(DYNAMIC_DIR):
        for archivo in os.listdir(DYNAMIC_DIR):
            if archivo.endswith(".py") and archivo != "__init__.py" and archivo != "historial_consumo.json":
                nom = archivo.replace(".py", "")
                tools_schema.append({
                    "name": nom,
                    "description": f"Ejecuta la automatización local ya existente '{nom}' en el sistema operativo.",
                    "parameters": {"type": "object", "properties": {}}
                })

    # Directiva base de comportamiento del Kernel
    system_instruction = (
        "Sos el nucleo de AGNUX OS. Responde de forma ultra corta.\n"
        "Si el usuario pide ver el hardware, usa 'tool_diagnostico_wrapper'.\n"
        "Si pide videos, peliculas, carreras o youtube, usa 'tool_reproductor_video'.\n"
        "Si pide algo que no existe y no podes resolver, usa 'autogenerar_nueva_tool'."
    )

    # 🏠 2. PROCESADOR INTERNO OLLAMA (HTTP Estándar OpenAI compatible)
    async def ejecutar_ollama_local(motivo_log: str):
        logger.info(f"🏠 PROCESANDO EN HOST LOCAL VIA OLLAMA ({modelo_actual}) -> Motivo: {motivo_log}")
        url_local = "http://127.0.0.1:11434/v1/chat/completions"
        
        # Adaptamos el esquema global al formato OpenAI que usa Ollama por HTTP
        openai_tools = [{"type": "function", "function": t} for t in tools_schema]
        
        payload_local = {
            "model": modelo_actual,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": payload.prompt}
            ],
            "tools": openai_tools,
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(url_local, json=payload_local, timeout=45.0)
                if res.status_code != 200:
                    return {"status": "error", "detail": f"Ollama HTTP Error: {res.text}"}
                
                choice = res.json()["choices"][0]["message"]
                
                # Captura del Function Calling en Ollama
                if "tool_calls" in choice and choice["tool_calls"]:
                    tool_call = choice["tool_calls"][0]["function"]
                    args = json.loads(tool_call["arguments"]) if isinstance(tool_call.get("arguments"), str) else tool_call.get("arguments", {})
                    resultado_local = ejecutar_herramienta_local(tool_call["name"], args)
                    return {"status": "success", "user": "user_cristian", "response": resultado_local}
                
                return {"status": "success", "user": "user_cristian", "response": choice.get("content", "").strip()}
            except Exception as e:
                return {"status": "error", "detail": f"Falla total en bus local: {str(e)}"}

    # --- RUTEO DE LA PETICIÓN EN BASE AL RUNTIME ACTIVO ---
    
    # CASO DIRECTO A CPU LOCAL
    if provider_actual == "local":
        return await ejecutar_ollama_local("Configuración por defecto")

    # CASO HÍBRIDO NUBE (CON REPLIEGUE SEGURO AUTOMÁTICO)
    elif provider_actual == "gemini":
        api_key = ""
        if os.path.exists(PROFILE_PATH):
            try:
                with open(PROFILE_PATH, "r") as f: api_key = json.load(f).get("api_key_guardada", "")
            except Exception: pass

        if not api_key:
            return await ejecutar_ollama_local("Bypass: API Key faltante")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        # Mapeo directo y simétrico del mismo esquema al dialecto de Google (Mayúsculas en los tipos)
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
                
                # FAILOVER TRIPLE-A: Si la nube pincha o da 429, Ollama toma el control en el acto
                if response.status_code != 200:
                    return await ejecutar_ollama_local(f"Bypass por error HTTP de la nube ({response.status_code})")
                    
                data = response.json()
                part = data['candidates'][0]['content']['parts'][0]

                # Telemetría de tokens en la nube
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

                # Captura del Function Calling en Gemini
                if "functionCall" in part:
                    func_call = part["functionCall"]
                    resultado_local = ejecutar_herramienta_local(func_call["name"], func_call.get("args", {}))
                    return {"status": "success", "user": "user_cristian", "response": resultado_local}

                return {"status": "success", "user": "user_cristian", "response": part.get("text", "").strip()}

            except Exception as e:
                return await ejecutar_ollama_local(f"Bypass por corte físico de red: {str(e)}")

    return {"status": "error", "detail": "Proveedor no configurado."}

# =====================================================================
# 🔌 STARTUP DAEMON
# =====================================================================
@app.on_event("startup")
async def startup_daemon():
    logger.info("🔍 AGNUX INITIAL BOOT: Configurando entorno...")
    prov_consola = os.getenv("AGNUX_IA_PROVIDER")
    if prov_consola:
        logger.info(f"⚡ PRIORIDAD DE CONSOLA: Forzando proveedor '{prov_consola}' de forma manual.")
    else:
        if os.path.exists(PROFILE_PATH):
            try:
                with open(PROFILE_PATH, "r") as f:
                    perfil = json.load(f)
                os.environ["AGNUX_IA_PROVIDER"] = perfil.get("proveedor_ia", "local")
                os.environ["AGNUX_ACTIVE_MODEL"] = perfil.get("modelo_ia_sugerido", "qwen2.5:1.5b")
            except Exception: pass
    logger.info(f"🚀 NÚCLEO CONFIGURADO -> Runtime: {os.getenv('AGNUX_IA_PROVIDER', 'local')}")