# agent_core.py
import os
import sys
import json
import importlib

# =====================================================================
# 🛠️ PARCHE ESTRICTO DE RUTAS PARA SUBPROCESOS DE LINUX/UVICORN
# =====================================================================
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from agno.agent import Agent
from agno.models.ollama import Ollama

# Importaciones de módulos nativos de herramientas
from tools.system_tools import obtener_diagnostico_hardware, gestionar_energia_equipo
from tools.multimedia_tools import ejecutar_musica_fondo, controlar_reproductor_global

# Configuración de directorios para herramientas en caliente
DYNAMIC_DIR = os.path.join(base_dir, "dynamic_tools")
os.makedirs(DYNAMIC_DIR, exist_ok=True)

if not os.path.exists(os.path.join(DYNAMIC_DIR, "__init__.py")):
    with open(os.path.join(DYNAMIC_DIR, "__init__.py"), "w") as f:
        f.write("")

# =====================================================================
# ⚡ HERRAMIENTAS FORMALES CON TIPADO NATIVO ESTRICTO (Para Agno)
# =====================================================================

def tool_diagnostico_wrapper(estado: str = None, accion: str = None) -> str:
    """
    Obtiene un reporte detallado del estado del hardware, uso de CPU, memoria RAM y disco en Lubuntu.
    """
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_diagnostico_wrapper'.")
    if estado or accion:
        print(f"   -> Descartando parámetros fantasma: estado={estado}, accion={accion}")
    try:
        resultado_dict = obtener_diagnostico_hardware()
        return json.dumps(resultado_dict, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error leyendo métricas de hardware: {str(e)}"

def tool_energia_wrapper(accion: str = "apagar", estado: str = None) -> str:
    """
    Gestiona la energía del equipo físico (apagar o reiniciar). El parámetro 'accion' debe ser 'apagar' o 'reinicio'.
    """
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_energia_wrapper' con accion: {accion}")
    try:
        return str(gestionar_energia_equipo(accion))
    except Exception as e:
        return f"Error en gestión de energía: {str(e)}"

def tool_musica_wrapper(busqueda: str = "lofi", accion: str = None, estado: str = None) -> str:
    """
    Busca una canción o mix en YouTube y lo reproduce de fondo usando MPV. Requiere el parámetro 'busqueda'.
    """
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_musica_wrapper' buscando: {busqueda}")
    try:
        return str(ejecutar_musica_fondo(busqueda))
    except Exception as e:
        return f"Error en subsistema multimedia: {str(e)}"

def tool_control_audio_wrapper(accion: str = "pausa", estado: str = None) -> str:
    """
    Controla el reproductor global MPV de fondo. El parámetro 'accion' debe ser 'pausa', 'reproducir' o 'detener'.
    """
    print(f"🔌 [TOOL CALL] El modelo invocó 'tool_control_audio_wrapper' con accion: {accion}")
    try:
        return str(controlar_reproductor_global(accion))
    except Exception as e:
        return f"Error controlando reproductor: {str(e)}"

def autogenerar_nueva_tool(nombre_funcion: str, codigo_python: str, descripcion_docstring: str) -> str:
    """
    Escribe un nuevo script de Python en caliente dentro de la carpeta 'dynamic_tools' para expandir las capacidades del sistema.
    
    Args:
        nombre_funcion (str): Nombre de la función en formato snake_case sin espacios.
        codigo_python (str): Bloque de código puro y funcional en Python.
        descripcion_docstring (str): Documentación formal explicando el propósito de la herramienta.
        
    Returns:
        str: Mensaje de éxito de la inyección en disco.
    """
    print(f"🛠️ [AUTOGÉNESIS] Creando nueva herramienta: '{nombre_funcion}'...")
    try:
        nombre_clean = nombre_funcion.strip().replace(" ", "_")
        nombre_archivo = f"{DYNAMIC_DIR}/{nombre_clean}.py"
        contenido_codigo = f'""\"\nDefinición autogenerada por AGNUX OS Core.\n""\"\n\ndef {nombre_clean}():\n    \"\"\"{descripcion_docstring}\"\"\"\n{codigo_python}\n'
        with open(nombre_archivo, "w") as f:
            f.write(contenido_codigo)
        return f"SUCCESS: Herramienta '{nombre_clean}' inyectada en disco."
    except Exception as e:
        return f"Error crítico de autogénesis: {str(e)}"

# =====================================================================
# 🧠 AGENTE CORE - CONFIGURACIÓN ESTÁNDAR COMPATIBLE
# =====================================================================
agnux_agent = Agent(
    model=Ollama(
        id="qwen2.5:0.5b",
        options={
            "num_thread": 2,       # Forzado estricto a los 2 hilos de tu Pentium G4400
            "num_predict": 128,    # Respuestas ágiles de consola
            "temperature": 0.0     # Precisión y determinismo puro
        }
    ),
    description="Sos el núcleo agéntico inmutable de AGNUX, operando de forma directa sobre la CPU host.",
    instructions=[
        "Analiza la intención del usuario para comandar el sistema operativo de forma precisa.",
        "Si te piden el estado de la memoria, CPU, temperaturas o disco, invoca la función 'tool_diagnostico_wrapper' sin pasar argumentos.",
        "Si te piden apagar o reiniciar el equipo, invoca 'tool_energia_wrapper' pasando el parámetro exacto 'accion' ('apagar' o 'reinicio').",
        "Si te piden reproducir música o un sonido de YouTube, invoca 'tool_musica_wrapper' pasando el término en el parámetro 'busqueda'.",
        "Si te piden pausar, reanudar o detener el reproductor, invoca 'tool_control_audio_wrapper' pasando en 'accion' los valores 'pausa', 'reproducir' o 'detener'.",
        "Si te piden una función de hardware o software que no posees instalada, diseña el código con 'autogenerar_nueva_tool'.",
        "Sé ultra directo, escueto y técnico. No agregues saludos, introducciones ni explicaciones de cortesía."
    ],
    # Al pasar la lista de funciones limpias con tipado nativo formal en la firma de Python, 
    # Agno genera el esquema JSON perfecto usando Pydantic nativo sin romper el diccionario de mapping.
    tools=[
        autogenerar_nueva_tool,
        tool_diagnostico_wrapper,
        tool_energia_wrapper,
        tool_musica_wrapper,
        tool_control_audio_wrapper
    ],
    markdown=False
)

# =====================================================================
# 🔄 MOTOR DE RECARGA EN CALIENTE
# =====================================================================
def recargar_herramientas_dinamicas():
    nuevas_tools = []
    if DYNAMIC_DIR not in sys.path:
        sys.path.append(DYNAMIC_DIR)

    try:
        archivos = os.listdir(DYNAMIC_DIR)
        for archivo in archivos:
            if archivo.endswith(".py") and archivo != "__init__.py":
                nombre_modulo = archivo.replace(".py", "")
                modulo = importlib.import_module(nombre_modulo)
                importlib.reload(modulo)
                funcion_objeto = getattr(modulo, nombre_modulo)
                nuevas_tools.append(funcion_objeto)
                
        if nuevas_tools:
            tools_base = [
                autogenerar_nueva_tool,
                tool_diagnostico_wrapper,
                tool_energia_wrapper,
                tool_musica_wrapper,
                tool_control_audio_wrapper
            ]
            agnux_agent.tools = tools_base + nuevas_tools
            agnux_agent.tools_schema = None
    except Exception as e:
        print(f"⚠️ Error en recarga dinámica del núcleo: {e}")