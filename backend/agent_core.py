# agent_core.py
import os
import sys
import json
import importlib
from typing import Literal

# =====================================================================
# 🛠️ PARCHE ESTRICTO DE RUTAS PARA SUBPROCESOS DE LINUX / UVICORN
# =====================================================================
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from agno.agent import Agent

# --- INSTANCIACIÓN DINÁMICA DEL PROVEEDOR DE IA ---
PROVEEDOR = os.getenv("AGNUX_IA_PROVIDER", "local")
MODELO_ID = os.getenv("AGNUX_ACTIVE_MODEL", "qwen2.5:1.5b")

if PROVEEDOR == "gemini":
    from agno.models.google import Gemini
    objeto_modelo = Gemini(id=MODELO_ID)
elif PROVEEDOR == "openai":
    from agno.models.openai import OpenAIChat
    objeto_modelo = OpenAIChat(id=MODELO_ID)
else:
    from agno.models.ollama import Ollama
    objeto_modelo = Ollama(id=MODELO_ID)

# Importaciones de módulos de herramientas estáticas nativas de AGNUX
from tools.system_tools import obtener_diagnostico_hardware, gestionar_energia_equipo
from tools.multimedia_tools import ejecutar_musica_fondo, controlar_reproductor_global

# Configuración del almacenamiento dinámico de herramientas autogeneradas
DYNAMIC_DIR = os.path.join(base_dir, "dynamic_tools")
os.makedirs(DYNAMIC_DIR, exist_ok=True)

if not os.path.exists(os.path.join(DYNAMIC_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_DIR, "__init__.py"), "w") as f:
        f.write("")

# =====================================================================
# 🧬 FUNCIÓN RAÍZ DE AUTOGÉNESIS (METAPROGRAMACIÓN EN CALIENTE)
# =====================================================================
def autogenerar_nueva_tool(nombre_funcion: str, codigo_python: str, descripcion_docstring: str) -> str:
    """
    OBLIGATORIA para crear, programar, listar cosas nuevas o desarrollar funciones de software o comandos que NO existan en el sistema.
    Si el usuario te pide listar archivos, interactuar con carpetas nuevas, crear scripts o automatizar tareas que no tenés en tus herramientas básicas, DEBÉS usar esta función para escribir el código.
    """
    print(f"🛠️ [AUTOGÉNESIS] El modelo determinó que falta una herramienta. Creando: '{nombre_funcion}'...")
    try:
        nombre_clean = nombre_funcion.strip().replace(" ", "_")
        nombre_archivo = f"{DYNAMIC_DIR}/{nombre_clean}.py"
        
        contenido_codigo = f'"""\nDefinición autogenerada por AGNUX OS Core.\n"""\n\ndef {nombre_clean}():\n    """{descripcion_docstring}"""\n{codigo_python}\n'
        
        with open(nombre_archivo, "w") as f:
            f.write(contenido_codigo)
            
        print(f"💾 [AUTOGÉNESIS] Código escrito con éxito en {nombre_archivo}")
        return f"SUCCESS: Herramienta '{nombre_clean}' inyectada en disco duro. Recargando matriz cognitiva..."
    except Exception as e:
        print(f"❌ [AUTOGÉNESIS ERROR] No se pudo escribir el script: {str(e)}")
        return f"Error crítico de autogénesis: {str(e)}"

# =====================================================================
# 🔌 WRAPPERS DE TELEMETRÍA Y CONTROL CON ENUMS ESTRICTOS (BLINDADOS)
# =====================================================================
# Cambiamos la definición para que absorba argumentos fantasmas
def tool_diagnostico_wrapper(**kwargs) -> str:
    """Muestra el estado actual del hardware de la máquina: uso de CPU, memoria RAM y espacio en disco duro."""
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_diagnostico_wrapper'. Argumentos ignorados: {kwargs}")
    res = obtener_diagnostico_hardware()
    return json.dumps(res, indent=2) if isinstance(res, dict) else str(res)

def tool_energia_wrapper(accion: Literal["apagar", "reiniciar"]) -> str:
    """Gestiona el encendido, apagado o reinicio físico del equipo host."""
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_energia_wrapper' con acción: {accion}")
    res = gestionar_energia_equipo(accion)
    return json.dumps(res, indent=2) if isinstance(res, dict) else str(res)

def tool_musica_wrapper(busqueda_o_url: str) -> str:
    """Busca y reproduce canciones, música o audios de YouTube de fondo en los parlantes del sistema operativo."""
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_musica_wrapper' buscando: {busqueda_o_url}")
    res = ejecutar_musica_fondo(busqueda_o_url)
    return str(res)

def tool_control_audio_wrapper(accion: Literal["pausa", "reproducir", "detener"]) -> str:
    """Controla el estado del reproductor de música de fondo (pausar, reanudar o detener de raíz el audio de mpv)."""
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_control_audio_wrapper' con acción: {accion}")
    res = controlar_reproductor_global(accion)
    return str(res)

# Lista base inmutable de herramientas del Kernel
TOOLS_BASE = [
    autogenerar_nueva_tool, 
    tool_diagnostico_wrapper, 
    tool_energia_wrapper,
    tool_musica_wrapper,
    tool_control_audio_wrapper
]

# =====================================================================
# 🧠 INICIALIZACIÓN DEL AGENTE CORE DE AGNUX (COMPLETAMENTE LIMPIO)
# =====================================================================
agnux_agent = Agent(
    model=objeto_modelo,
    description=None,
    instructions=None,
    system_message=None,
    add_datetime_to_instructions=False,
    tools=TOOLS_BASE,
    markdown=False
)

# =====================================================================
# 🔄 RECARGA COGNITIVA EN CALIENTE (DYNAMIC MODULE IMPORT)
# =====================================================================
def recargar_herramientas_dinamicas():
    """
    Escanea la carpeta de herramientas generadas por el modelo, las compila e
    inyecta sus objetos nativos de Python de forma limpia en la estructura del agente.
    """
    nuevas_tools = []
    if DYNAMIC_DIR not in sys.path:
        sys.path.append(DYNAMIC_DIR)

    try:
        for archivo in os.listdir(DYNAMIC_DIR):
            if archivo.endswith(".py") and archivo != "__init__.py" and archivo != "historial_consumo.json":
                nombre_modulo = archivo.replace(".py", "")
                
                modulo = importlib.import_module(f"dynamic_tools.{nombre_modulo}")
                importlib.reload(modulo)
                
                funcion_objeto = getattr(modulo, nombre_modulo)
                nuevas_tools.append(funcion_objeto)
                
        # Seteamos la lista de herramientas combinada de forma limpia
        agnux_agent.tools = TOOLS_BASE + nuevas_tools
        
    except Exception as e:
        print(f"⚠️ Error en recarga dinámica del núcleo: {e}")