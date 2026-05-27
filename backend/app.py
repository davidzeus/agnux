# app.py
import os
import sys
import logging
import subprocess
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# =====================================================================
# 🛠️ PARCHE ESTRICTO DE RUTAS PARA SUBPROCESOS DE LINUX / UVICORN
# =====================================================================
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

# Configuración de los Logs industriales en la consola
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("AGNUX_API")

PROFILE_PATH = os.path.join(base_dir, "system_profile.json")

# =====================================================================
# 🔍 FUNCIÓN NATIVA DE INTROSPECCIÓN DE HARDWARE (CON MEMORIA COGNITIVA)
# =====================================================================
def auto_evaluar_hardware_host() -> dict:
    """
    Censa los componentes físicos del host Linux. Si encuentra un perfil previo
    con credenciales guardadas, se saltea el cuestionario para permitir un 
    arranque silencioso y fluido tras eventos de autogénesis o recargas.
    """
    # 1. Intentar cargar memoria de configuración previa
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r") as f:
                perfil_guardado = json.load(f)
            
            # Si el perfil es válido y ya tiene una definición de entorno, salteamos el input
            if perfil_guardado.get("proveedor_ia") in ["local", "gemini", "openai"] and perfil_guardado.get("modelo_ia_sugerido"):
                return perfil_guardado
        except Exception as e:
            logger.warning(f"⚠️ No se pudo procesar el perfil persistente existente. Forzando cuestionario: {e}")

    # 2. Si no hay perfil previo, generamos la plantilla base analizando los fierros
    perfil = {
        "cpu_modelo": "Desconocido",
        "cpu_nucleos": 2,
        "ram_total_gb": 4,
        "posee_gpu_nvidia": False,
        "proveedor_ia": "local",        # 'local', 'gemini', 'openai'
        "modelo_ia_sugerido": "qwen2.5:1.5b",
        "teclado_layout": "us",
        "disco_raiz_libre_gb": 0,
        "api_key_guardada": ""
    }
    
    try:
        # Censar componentes físicos del Kernel
        perfil["cpu_modelo"] = subprocess.getoutput("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2").strip()
        perfil["cpu_nucleos"] = int(subprocess.getoutput("nproc"))

        with open("/proc/meminfo", "r") as f:
            for linea in f:
                if "MemTotal" in linea:
                    ram_kb = int(linea.split()[1])
                    perfil["ram_total_gb"] = round(ram_kb / (1024 * 1024))
                    break

        # 3. INTERFAZ INTERACTIVA EN CONSOLA (Solo se ejecuta la primera vez)
        print("\n" + "="*60)
        print(" 🌐 CONFIGURACIÓN INICIAL DEL MOTOR DE INTELIGENCIA DE AGNUX")
        print("="*60)
        print(" Podés usar el procesamiento local en tu procesador o")
        print(" delegar la carga a la nube si poseés una suscripción.")
        print(" ⚠️ ¡ATENCIÓN!: El uso de la nube CONSUMIRÁ TOKENS de tu cuenta.")
        print("="*60)
        
        opcion = input("¿Deseás activar una suscripción externa via API Key? (si/no): ").strip().lower()
        
        if opcion in ["si", "s", "yes"]:
            print("\n Seleccioná el proveedor externo de tu preferencia:")
            print(" [1] Google Gemini (Modelo sugerido: gemini-2.5-flash)")
            print(" [2] OpenAI ChatGPT (Modelo sugerido: gpt-4o-mini)")
            prov_opcion = input(" Elección (1 o 2): ").strip()
            
            if prov_opcion == "1":
                key = input(" 🔑 Introducí tu GEMINI_API_KEY: ").strip()
                if key:
                    perfil["proveedor_ia"] = "gemini"
                    perfil["modelo_ia_sugerido"] = "gemini-2.5-flash"
                    perfil["api_key_guardada"] = key
            elif prov_opcion == "2":
                key = input(" 🔑 Introducí tu OPENAI_API_KEY: ").strip()
                if key:
                    perfil["proveedor_ia"] = "openai"
                    perfil["modelo_ia_sugerido"] = "gpt-4o-mini"
                    perfil["api_key_guardada"] = key
        
        # 4. Estrategia de repliegue local si se rechaza la nube o las llaves están vacías
        if perfil["proveedor_ia"] == "local":
            check_gpu = subprocess.run("command -v nvidia-smi && nvidia-smi", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if check_gpu.returncode == 0 and b"failed" not in check_gpu.stderr:
                perfil["posee_gpu_nvidia"] = True
                perfil["modelo_ia_sugerido"] = "qwen-test:latest"
            else:
                perfil["posee_gpu_nvidia"] = False
                if perfil["cpu_nucleos"] <= 4 or perfil["ram_total_gb"] < 12:
                    perfil["modelo_ia_sugerido"] = "qwen2.5:1.5b"
                else:
                    perfil["modelo_ia_sugerido"] = "qwen-test:latest"

        # Mapeo periférico final y espacio físico
        layout = subprocess.getoutput("localectl status | grep 'X11 Layout' | cut -d: -f2").strip()
        if layout: perfil["teclado_layout"] = layout
        statvfs = os.statvfs('/')
        perfil["disco_raiz_libre_gb"] = round((statvfs.f_bavail * statvfs.f_frsize) / (1024 ** 3))

        # Escribimos el perfil en limpio en el almacenamiento inmutable
        with open(PROFILE_PATH, "w") as f:
            json.dump(perfil, f, indent=4)
            
        print("="*60 + "\n")
        return perfil
    except Exception as e:
        logger.error(f"Falla crítica en subsistema de introspección nativa: {e}")
        return perfil

# =====================================================================
# 🚀 INICIALIZACIÓN DE LA API NATIVA FASTAPI
# =====================================================================
app = FastAPI(
    title="AGNUX Core Inmutable Engine",
    description="Motor de orquestación agéntica y lógica de bajo nivel para AGNUX OS.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agnux_state = {
    "usuario_activo": "user_cristian",
    "hardware": {}
}

class SystemWindowManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def emitir_evento_sistema(self, evento: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(evento)
            except Exception:
                pass

window_manager = SystemWindowManager()

class TaskbarPrompt(BaseModel):
    prompt: str

# =====================================================================
# 📥 ENDPOINT DE ENTRADA PRINCIPAL (BYPASS HÍBRIDO TOTAL)
# =====================================================================
@app.post("/api/system/intent")
async def procesar_intencion_global(payload: TaskbarPrompt):
    logger.info(f"📥 SOLICITUD RECIBIDA -> Prompt: '{payload.prompt}'")
    
    # Sincronizamos e importamos las herramientas estáticas y dinámicas
    from agent_core import recargar_herramientas_dinamicas, agnux_agent, DYNAMIC_DIR
    recargar_herramientas_dinamicas()
    
    # Construcción inyectada del contexto inmutable del sistema operativo
    prompt_con_instrucciones = (
        "CONTEXTO E INSTRUCCIONES INMUTABLES DE AGNUX OS:\n"
        "1. Sos el nucleo de autogenesis del sistema operativo. Tu fuerte es la programacion de bajo nivel en Python/Bash.\n"
        "2. Si el usuario te pide una tarea, comando o accion que requiere interactuar con el sistema (como listar archivos de una carpeta, crear scripts, controlar hardware, etc.) y NO TENES una herramienta especifica para eso en tu lista, DEBES LLAMAR INMEDIATAMENTE a la funcion 'autogenerar_nueva_tool' para programarla en caliente.\n"
        "3. Tenes prohibido responder con texto simulando una falla o diciendo que no podes si antes no creaste el script de automatizacion correspondiente.\n"
        "4. Al usar 'autogenerar_nueva_tool', escribe codigo Python puro, limpio, usando librerias estandar (como 'os' o 'subprocess') para resolver el problema real en el host.\n"
        "5. Una vez ejecutada la herramienta, reporta el resultado de la operacion de forma concisa.\n\n"
        f"PETICION DEL UNIVERSO USUARIO: {payload.prompt}"
    )
    
    logger.info("🧠 Derivando bucle cognitivo. Procesando razonamiento...")
    inicio_ia = datetime.now()
    
    # --- CAMINO A: PUENTE NATIVO CON GOOGLE GEMINI SDK (BYPASS DE AGNO) ---
    if os.getenv("AGNUX_IA_PROVIDER") == "gemini":
        try:
            import google.generativeai as genai
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            
            import agent_core
            lista_funciones = [
                agent_core.autogenerar_nueva_tool,
                agent_core.tool_diagnostico_wrapper,
                agent_core.tool_energia_wrapper,
                agent_core.tool_musica_wrapper,
                agent_core.tool_control_audio_wrapper
            ]
            
            # Sumamos las herramientas dinámicas generadas previamente al mapa oficial del SDK
            if os.path.exists(DYNAMIC_DIR):
                import importlib
                for archivo in os.listdir(DYNAMIC_DIR):
                    if archivo.endswith(".py") and archivo != "__init__.py":
                        nombre_mod = archivo.replace(".py", "")
                        modulo = importlib.import_module(nombre_mod)
                        lista_funciones.append(getattr(modulo, nombre_mod))

            model = genai.GenerativeModel(
                model_name=os.getenv("AGNUX_ACTIVE_MODEL", "gemini-2.5-flash"),
                tools=lista_funciones
            )
            
            # Iniciamos chat con ejecución de funciones en bucle automático local activada
            chat = model.start_chat(enable_automatic_function_calling=True)
            
            loop = asyncio.get_event_loop()
            respuesta = await loop.run_in_executor(None, chat.send_message, prompt_con_instrucciones)
            
            tiempo_total = (datetime.now() - inicio_ia).total_seconds()
            logger.info(f"✅ GEMINI NATIVO RESPONDIÓ exitosamente en {tiempo_total:.2f} segundos.")
            
            # EXTRAER RESPUESTA FINAL POST-EJECUCIÓN DEL HISTORIAL (Evita el bug de Parts vacíos)
            texto_final = chat.history[-1].parts[0].text
            
            return {
                "status": "success",
                "user": agnux_state["usuario_activo"],
                "response": texto_final if texto_final else "Herramienta ejecutada de forma correcta."
            }
            
        except Exception as e:
            logger.error(f"❌ Error en el puente nativo de Gemini: {str(e)}")
            return {"status": "error", "detail": f"Gemini Native Bridge Error: {str(e)}"}

    # --- CAMINO B: REPLIEGUE SEGURO LOCAL CON MODELO OLLAMA ---
    else:
        loop = asyncio.get_event_loop()
        try:
            respuesta_agente = await loop.run_in_executor(None, agnux_agent.run, payload.prompt)
            tiempo_total = (datetime.now() - inicio_ia).total_seconds()
            logger.info(f"✅ OLLAMA LOCAL RESPONDIÓ exitosamente en {tiempo_total:.2f} segundos.")
            return {
                "status": "success",
                "user": agnux_state["usuario_activo"],
                "response": respuesta_agente.content
            }
        except Exception as e:
            logger.error(f"❌ Error en procesamiento local de Agno: {str(e)}")
            return {"status": "error", "detail": str(e)}

@app.websocket("/ws/system-events")
async def system_events_endpoint(websocket: WebSocket):
    await window_manager.connect(websocket)
    logger.info("🔌 Canal WebSocket establecido con la interfaz de usuario.")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        window_manager.disconnect(websocket)
        logger.info("🔌 Conexión WebSocket finalizada por el cliente.")

# =====================================================================
# 🔌 ARRANQUE SEGURO Y CONTROLADO (STARTUP DAEMON)
# =====================================================================
@app.on_event("startup")
async def arrancar_servicios_nucleo():
    logger.info("🔍 AGNUX INITIAL BOOT: Interrogando al Kernel de Linux...")
    
    perfil_detectado = auto_evaluar_hardware_host()
    agnux_state["hardware"] = perfil_detectado
    
    os.environ["AGNUX_IA_PROVIDER"] = perfil_detectado.get("proveedor_ia", "local")
    os.environ["AGNUX_ACTIVE_MODEL"] = perfil_detectado.get("modelo_ia_sugerido", "qwen2.5:1.5b")
    
    if perfil_detectado.get("proveedor_ia") == "gemini":
        clave = perfil_detectado.get("api_key_guardada", "")
        os.environ["GEMINI_API_KEY"] = clave
        os.environ["GOOGLE_API_KEY"] = clave
        logger.info(f"🌐 MODO HÍBRIDO ACTIVADO: Cerebro en la nube via Google Gemini API ({os.environ['AGNUX_ACTIVE_MODEL']}).")
    elif perfil_detectado.get("proveedor_ia") == "openai":
        clave = perfil_detectado.get("api_key_guardada", "")
        os.environ["OPENAI_API_KEY"] = clave
        logger.info(f"🌐 MODO HÍBRIDO ACTIVADO: Cerebro en la nube via OpenAI ChatGPT API ({os.environ['AGNUX_ACTIVE_MODEL']}).")
    else:
        logger.info(f"🏠 MODO LOCAL ACTIVADO: Procesando en host físico via Ollama ({os.environ['AGNUX_ACTIVE_MODEL']}).")
        if not perfil_detectado.get("posee_gpu_nvidia", False):
            os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

    logger.info("🚀 NÚCLEO INDUSTRIAL DE AGNUX: Completamente configurado y activo en Localhost.")