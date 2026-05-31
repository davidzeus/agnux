# agent_core.py
# =====================================================================
# 🧠 AGNUX OS — NÚCLEO DEL AGENTE COGNITIVO (Motor Agno Nativo)
# =====================================================================
# REGLA CONSTITUCIONAL: Está TAXATIVAMENTE PROHIBIDO el uso de guiones
# bajos ('_') en identificadores de usuario, nombre de terminal, variables
# de contexto del host o nombre de herramienta dinámica.
# Usar SIEMPRE guiones medios ('-') o alfanumérico plano en minúsculas.
# =====================================================================
import os
import sys
import json
import importlib
from typing import Literal

# =====================================================================
# 🛠️ PARCHE DE RUTAS PARA SUBPROCESOS DE LINUX / UVICORN
# Garantiza que las importaciones relativas funcionen al ser ejecutadas
# desde subdirectorios (uvicorn, subprocesos, etc.)
# =====================================================================
base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from agno.agent import Agent
from core.config import logger, DYNAMIC_DIR

# =====================================================================
# 🤖 SELECCIÓN DINÁMICA DEL PROVEEDOR DE IA
# Configurable vía variables de entorno sin redeployar
# =====================================================================
PROVEEDOR = os.getenv("AGNUX_IA_PROVIDER", "local")
MODELO_ID  = os.getenv("AGNUX_ACTIVE_MODEL", "qwen2.5:1.5b")

if PROVEEDOR == "gemini":
    from agno.models.google import Gemini
    objeto_modelo = Gemini(id=MODELO_ID)
elif PROVEEDOR == "openai":
    from agno.models.openai import OpenAIChat
    objeto_modelo = OpenAIChat(id=MODELO_ID)
else:
    # Proveedor por defecto: Ollama local en el SR630
    from agno.models.ollama import Ollama
    objeto_modelo = Ollama(
        id=MODELO_ID,
        host=os.getenv("OLLAMA_HOST", "http://10.10.0.48:11434")
    )

# =====================================================================
# 🔌 IMPORTACIONES DE HERRAMIENTAS ESTÁTICAS NATIVAS DEL HOST
# =====================================================================
from tools.system_tools    import obtener_diagnostico_hardware, gestionar_energia_equipo
from tools.multimedia_tools import ejecutar_musica_fondo, controlar_reproductor_global
from tools.sandbox_tool    import ejecutar_en_docker_sync

# =====================================================================
# 🔧 HERRAMIENTAS BASE — DEFINICIÓN DE WRAPPERS BLINDADOS
# Todos los parámetros de usuario/terminal usan guiones medios.
# Los wrappers absorben **kwargs fantasmas que Agno pueda inyectar.
# =====================================================================

def tool_diagnostico_wrapper(**kwargs) -> str:
    """
    Muestra el estado actual del hardware de la máquina host:
    uso de CPU, memoria RAM y espacio en disco duro.
    No requiere argumentos.
    """
    logger.info(f"🔌 [TOOL] tool-diagnostico invocada. kwargs ignorados: {kwargs}")
    res = obtener_diagnostico_hardware()
    return json.dumps(res, indent=2, ensure_ascii=False) if isinstance(res, dict) else str(res)


def tool_energia_wrapper(accion: Literal["apagar", "reiniciar"]) -> str:
    """
    Gestiona el encendido, apagado o reinicio físico del equipo host.
    Parámetros:
      - accion: 'apagar' o 'reiniciar'
    """
    logger.info(f"🔌 [TOOL] tool-energia invocada con accion='{accion}'")
    res = gestionar_energia_equipo(accion)
    return json.dumps(res, indent=2, ensure_ascii=False) if isinstance(res, dict) else str(res)


def tool_musica_wrapper(busqueda_o_url: str) -> str:
    """
    Busca y reproduce canciones, música o audios de YouTube de fondo
    en los parlantes del sistema operativo del host.
    Parámetros:
      - busqueda_o_url: término de búsqueda o URL directa de YouTube
    """
    logger.info(f"🔌 [TOOL] tool-musica invocada. Búsqueda: '{busqueda_o_url}'")
    return str(ejecutar_musica_fondo(busqueda_o_url))


def tool_control_audio_wrapper(accion: Literal["pausa", "reproducir", "detener"]) -> str:
    """
    Controla el estado del reproductor de música de fondo del sistema
    (pausar, reanudar o detener el proceso mpv).
    Parámetros:
      - accion: 'pausa', 'reproducir' o 'detener'
    """
    logger.info(f"🔌 [TOOL] tool-control-audio invocada con accion='{accion}'")
    return str(controlar_reproductor_global(accion))


def open_system_app(app_id: str) -> str:
    """
    Ordena al cliente web de AGNUX que abra una aplicación de sistema
    en modo ventana flotante dentro del escritorio.
    Usá esto cuando el usuario pida abrir una app, calculadora, editor,
    terminal, o cualquier panel del sistema operativo.
    Parámetros:
      - app-id: identificador de la aplicación a abrir.
        Valores válidos: 'calc', 'terminal', 'files', 'settings',
        'hyper-island', 'notes', 'network-monitor'
    """
    logger.info(f"🔌 [TOOL] open-system-app invocada. app-id='{app_id}'")
    # Este tool emite un evento CLIENT-SIDE que el orquestador intercepta
    # y despacha como SSE CREATE-WINDOW al frontend Angular.
    return json.dumps({"__agnux_event": "OPEN-SYSTEM-APP", "app-id": app_id})


def open_local_media(media_type: str, query: str = "") -> str:
    """
    Abre o busca contenido multimedia local o en streaming dentro
    del escritorio de AGNUX (pestaña de Chromium en modo kiosco).
    Parámetros:
      - media-type: tipo de media. Valores válidos: 'youtube', 'spotify',
        'netflix', 'youtube-music', 'local-video', 'local-audio'
      - query: término de búsqueda opcional (nombre de canción, película, etc.)
    """
    logger.info(f"🔌 [TOOL] open-local-media invocada. media-type='{media_type}', query='{query}'")
    return json.dumps({
        "__agnux_event": "OPEN-LOCAL-MEDIA",
        "media-type": media_type,
        "query": query
    })


def autogenerar_nueva_tool(nombre_funcion: str, descripcion_docstring: str) -> str:
    """
    OBLIGATORIA para crear, programar o desarrollar funciones de software o
    comandos que NO existan en el sistema.
    Si el usuario pide listar archivos, interactuar con carpetas, crear scripts
    o automatizar tareas que no están en las herramientas actuales, DEBÉS usar
    esta función.
    REGLA: el nombre de la función y el archivo físico DEBEN usar guiones medios
    (ej: 'global-control-bomba', 'user-listar-archivos').
    Parámetros:
      - nombre_funcion: nombre de la función nueva (usar guiones medios, sin .py)
      - descripcion_docstring: descripción del propósito de la herramienta
    """
    logger.info(f"🛠️ [AUTOGÉNESIS] Delegando herramienta: '{nombre_funcion}' al Coder Model...")
    try:
        # Normalización ESTRICTA: sólo guiones medios, minúsculas, sin espacios
        nombre_normalizado = (
            nombre_funcion.strip()
            .lower()
            .replace(" ", "-")
            .replace("_", "-")          # Prohibición constitucional de guiones bajos
            .rstrip(".py")
        )
        nombre_simbolo = nombre_normalizado.replace("-", "_")
        nombre_archivo = os.path.join(DYNAMIC_DIR, f"{nombre_normalizado}.py")

        coder_model = os.environ.get("AGNUX_CODER_MODEL", "deepseek-coder:1.5b")
        from agno.agent import Agent
        from agno.models.ollama import Ollama
        
        coder_agent = Agent(
            model=Ollama(id=coder_model),
            system_message="Sos un asistente experto en Python. Tu tarea es escribir CÓDIGO PURO. Nunca devuelvas explicaciones ni texto normal. Devuelve un bloque de código markdown ```python ... ``` con la implementación.",
            markdown=False
        )
        
        prompt = f"Escribe una función de Python completa llamada '{nombre_simbolo}' que acepte `**kwargs` y cumpla este propósito:\n\n{descripcion_docstring}\n\nIncluye todos los imports necesarios en la parte superior. Solo devuelve el bloque de código Python."
        
        respuesta_coder = coder_agent.run(prompt)
        codigo_python = respuesta_coder.content if hasattr(respuesta_coder, "content") else str(respuesta_coder)

        # Limpiar código si viene con fence de markdown
        codigo_depurado = codigo_python.strip()
        if codigo_depurado.startswith("```"):
            partes = codigo_depurado.split("```")
            codigo_depurado = partes[1].replace("python", "", 1).strip() if len(partes) > 1 else codigo_depurado
            if codigo_depurado.endswith("```"):
                codigo_depurado = codigo_depurado[:-3].strip()

        contenido_final = (
            f'"""\n'
            f'Auto-generada por AGNUX OS Core (Modelo: {coder_model}).\n'
            f'Nombre del módulo: {nombre_normalizado}\n'
            f'{descripcion_docstring}\n'
            f'"""\n\n'
            f'{codigo_depurado}\n'
        )

        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(contenido_final)

        logger.info(f"💾 [AUTOGÉNESIS] Herramienta instalada con éxito en: {nombre_archivo}")
        return f"SUCCESS: Herramienta '{nombre_normalizado}' inyectada en disco. Recargando matriz cognitiva..."
    except Exception as e:
        logger.error(f"❌ [AUTOGÉNESIS] Falla crítica: {e}")
        return f"Error crítico de autogénesis: {str(e)}"


# =====================================================================
# 🐳 SANDBOX DE EVALUACIÓN DE CÓDIGO (Docker Ephemeral)
# =====================================================================
import asyncio as _asyncio

def evaluar_codigo_sandbox(codigo: str, lenguaje: str, descripcion: str = "") -> str:
    """
    Evalúa y prueba un bloque de código en un contenedor Docker aislado
    ANTES de enviarlo a la interfaz o inyectarlo al sistema.
    Hacer SIEMPRE esto cuando el usuario pida:
    - Generar código que se va a mostrar en el escritorio
    - Crear un widget, script o componente nuevo
    - Ejecutar código que autogeneraste para validar que funciona
    - Probar cualquier función antes de agregarla al sistema

    El contenedor es efímero: se crea, ejecuta y destruye automáticamente.
    Sin acceso a internet. Sin escritura en disco del host.
    Si el código falla, el resultado contiene el error para que puedas
    corregirlo y volver a intentarlo (máximo 3 intentos).

    Parámetros:
      - codigo: el código fuente completo a evaluar (sin fences markdown)
      - lenguaje: 'python', 'javascript' o 'bash'
      - descripcion: descripción breve de qué se espera que haga el código
    """
    logger.info(f"🐳 [SANDBOX] Evaluando código {lenguaje} ({len(codigo)} chars) en Docker...")

    # Limpiar fence de markdown si el LLM lo incluyó por error
    codigo_limpio = codigo.strip()
    if codigo_limpio.startswith("```"):
        partes = codigo_limpio.split("```")
        codigo_limpio = partes[1].replace(lenguaje, "", 1).strip() if len(partes) > 1 else codigo_limpio

    # Ejecutar en thread bloqueante para no frenar el event loop de FastAPI
    try:
        loop   = _asyncio.get_event_loop()
        result = loop.run_until_complete(
            _asyncio.to_thread(ejecutar_en_docker_sync, codigo_limpio, lenguaje)
        ) if loop.is_running() else _asyncio.run(
            _asyncio.to_thread(ejecutar_en_docker_sync, codigo_limpio, lenguaje)
        )
    except RuntimeError:
        # Fallback síncrono si el event loop no está disponible en este contexto
        result = ejecutar_en_docker_sync(codigo_limpio, lenguaje)

    # Empaquetamos la señal especial para que el orquestador la intercepte
    result["__sandbox_result"] = True
    result["codigo"]           = codigo_limpio
    result["descripcion"]      = descripcion

    logger.info(
        f"{'✅' if result['ok'] else '❌'} [SANDBOX] "
        f"{'OK' if result['ok'] else 'FAIL'} "
        f"— exit={result['exit-code']} — {result['execution-ms']}ms"
    )
    return json.dumps(result, ensure_ascii=False)


# =====================================================================
# 📌 ACCESOS DIRECTOS DEL ESCRITORIO (Desktop Shortcuts)
# =====================================================================
def crear_acceso_directo(
    nombre: str = "",
    icono: str = "📌",
    tipo: str = "app",
    destino: str = "",
    descripcion: str = "",
    **kwargs
) -> str:
    """
    Crea un acceso directo (icono) en el escritorio de AGNUX.
    El usuario puede hacer clic en él para abrir apps, URLs o ejecutar
    comandos directamente sin escribir en la barra de comandos.
    Ideal para crear launchers rápidos de las herramientas favoritas.

    Parámetros:
      - nombre: texto visible debajo del icono (ej: 'Terminal', 'Spotify')
      - icono: emoji que representa el acceso directo (ej: '💻', '🎵', '🗂️')
      - tipo: qué hace al hacer clic. Valores válidos:
              'app'     → abre una app del sistema (usa 'app-id' en destino)
              'url'     → abre una URL en nueva pestaña
              'command' → ejecuta un prompt en la barra de comandos
      - destino: el target según el tipo.
               Si tipo='app'     → ej: 'terminal', 'calc', 'files'
               Si tipo='url'     → ej: 'https://github.com'
               Si tipo='command' → ej: 'muestrame el estado del hardware'
      - descripcion: tooltip al hacer hover sobre el icono
    """
    # Workaround para LLMs locales que anidan los argumentos
    if "params" in kwargs and isinstance(kwargs["params"], dict):
        p = kwargs["params"]
        nombre = p.get("nombre", nombre)
        icono = p.get("icono", icono)
        tipo = p.get("tipo", tipo)
        destino = p.get("destino", destino)
        descripcion = p.get("descripcion", descripcion)

    logger.info(f"📌 [SHORTCUT] Creando acceso directo: '{nombre}' tipo='{tipo}' destino='{destino}'")
    return json.dumps({
        "__agnux_event": "ADD-SHORTCUT",
        "id":          f"shortcut-{nombre.lower().replace(' ', '-').replace('_', '-')}-{int(__import__('time').time())}",
        "nombre":      nombre,
        "icono":       icono,
        "tipo":        tipo,
        "destino":     destino,
        "descripcion": descripcion,
    }, ensure_ascii=False)


# =====================================================================
# ℹ️ MANIFIESTO DE CAPACIDADES DEL SISTEMA
# =====================================================================
def obtener_info_sistema() -> str:
    """
    Retorna el manifiesto completo de capacidades del sistema AGNUX OS.
    Usar cuando el usuario pregunte qué podés hacer, cuáles son tus
    herramientas, cómo te llamar, qué funciones tenés, o cualquier
    variación de '\u00bfqué podés hacer?'.
    No requiere parámetros.
    """
    manifiesto = {
        "__agnux_event": "ADD-SHORTCUT",   # No usar, es solo marcador interno
        "sistema":       "AGNUX OS Cognitive Kernel",
        "version":       "2.0 — Motor Agno Nativo",
        "capacidades": [
            {
                "categoria":   "🔧 Sistema & Hardware",
                "herramientas": [
                    {
                        "nombre":      "Diagnóstico de Hardware",
                        "comando":     "Ej: 'cómo está el hardware', 'uso de CPU'",
                        "descripcion": "Muestra el estado en tiempo real del CPU, RAM y disco del servidor SR630.",
                    },
                    {
                        "nombre":      "Gestión de Energía",
                        "comando":     "Ej: 'apagá el equipo', 'reiniciá el servidor'",
                        "descripcion": "Controla el apagado o reinicio físico del host de forma segura.",
                    },
                ]
            },
            {
                "categoria":   "🎵 Multimedia",
                "herramientas": [
                    {
                        "nombre":      "Reproducción de Música",
                        "comando":     "Ej: 'poné lofi hip hop', 'reproducir Pink Floyd'",
                        "descripcion": "Busca y reproduce música de YouTube en los parlantes del host con mpv.",
                    },
                    {
                        "nombre":      "Control de Audio",
                        "comando":     "Ej: 'pausá la música', 'detené el audio'",
                        "descripcion": "Pausa, reanuda o detiene el reproductor de fondo.",
                    },
                    {
                        "nombre":      "Abrir Plataforma de Streaming",
                        "comando":     "Ej: 'abrí Spotify', 'abrí Netflix', 'YouTube Music'",
                        "descripcion": "Abre Spotify, Netflix o YouTube Music en el navegador del escritorio.",
                    },
                ]
            },
            {
                "categoria":   "🖥️ Escritorio & UI",
                "herramientas": [
                    {
                        "nombre":      "Cambiar Fondo de Pantalla",
                        "comando":     "Ej: 'cambiá el fondo a una imagen de espacio'",
                        "descripcion": "Cambia el wallpaper del escritorio con cualquier URL de imagen.",
                    },
                    {
                        "nombre":      "Aplicar Tema CSS",
                        "comando":     "Ej: 'modo hacker', 'tema cyberpunk rojo', 'estilo Windows XP'",
                        "descripcion": "Rediseña toda la interfaz inyectando CSS en tiempo real, sin recargar.",
                    },
                    {
                        "nombre":      "Abrir App del Sistema",
                        "comando":     "Ej: 'abrí la terminal', 'abrí la calculadora', 'abrí el monitor de red'",
                        "descripcion": "Abre apps del sistema como ventanas flotantes en el escritorio.",
                    },
                    {
                        "nombre":      "Crear Acceso Directo",
                        "comando":     "Ej: 'creá un acceso directo a Spotify', 'piné la terminal al escritorio'",
                        "descripcion": "Agrega iconos clickeables al escritorio para acceso rápido a apps, URLs o comandos.",
                    },
                ]
            },
            {
                "categoria":   "🧠 IA & Autogénesis",
                "herramientas": [
                    {
                        "nombre":      "Crear Nueva Herramienta",
                        "comando":     "Ej: 'creá una herramienta para listar archivos'",
                        "descripcion": "Programa en caliente una nueva función Python y la inyecta en el sistema sin reiniciar.",
                    },
                    {
                        "nombre":      "Sandbox de Código",
                        "comando":     "Ej: 'ejecutá este script Python', 'probá este código'",
                        "descripcion": "Evalua código en un contenedor Docker aislado antes de enviarlo al escritorio.",
                    },
                ]
            },
            {
                "categoria":   "🔐 Google Workspace (requiere conexión)",
                "herramientas": [
                    {
                        "nombre":      "Gmail, Drive, Calendar",
                        "comando":     "Ej: 'abrí Gmail', 'nueva hoja de cálculo'",
                        "descripcion": "Interacción con toda la suite de Google si la cuenta está vinculada.",
                    },
                ]
            },
        ]
    }
    # Retornamos como evento para que el orquestador lo despache como
    # ventana de ayuda en el escritorio
    return json.dumps({
        "__agnux_event": "SHOW-SYSTEM-INFO",
        "manifiesto":    manifiesto,
    }, ensure_ascii=False)
# Estas tools son el "firmware" del agente. Siempre presentes.
# =====================================================================
TOOLS_BASE = [
    autogenerar_nueva_tool,
    tool_diagnostico_wrapper,
    tool_energia_wrapper,
    tool_musica_wrapper,
    tool_control_audio_wrapper,
    open_system_app,
    open_local_media,
    evaluar_codigo_sandbox,
    crear_acceso_directo,
    obtener_info_sistema,
]

# =====================================================================
# WRAPPERS PARA SYSTEM_TOOLS
# Agno requiere que TODAS las herramientas descritas en el system_prompt
# existan como funciones reales en la lista de tools del agente.
# Las descripciones deben ser explícitas para modelos pequeños.
# =====================================================================

def calculateExpression(expression: str) -> str:
    """
    ¡USAR SIEMPRE PARA CUALQUIER CÁLCULO MATEMÁTICO!
    Evalúa expresiones aritméticas complejas en el Host.
    Nunca resuelvas cálculos mentalmente ni respondas con texto. Llama a esta herramienta.
    
    Args:
        expression (str): La expresión matemática a calcular (ej: '3 + 3').
    """
    return json.dumps({"__agnux_event": "CALCULATE-EXPRESSION", "expression": expression})

def setWallpaper(imageUrl: str) -> str:
    """Cambia el fondo de pantalla del escritorio usando una URL de imagen válida."""
    return json.dumps({"__agnux_event": "SET-WALLPAPER", "imageUrl": imageUrl})

def applyCssTheme(cssCode: str) -> str:
    """
    ¡USAR SIEMPRE PARA CAMBIAR EL TEMA O COLOR VISUAL!
    Aplica un nuevo estilo físico (CSS) a la interfaz de AGNUX OS. 
    Llama a esta herramienta en lugar de decirle al usuario que aplicaste el estilo.
    
    Args:
        cssCode (str): El código CSS a inyectar, modificando variables en :root (ej: ':root { --agnux-bg-color: #000; }').
    """
    return json.dumps({"__agnux_event": "SET-THEME", "cssCode": cssCode})

def googleWorkspaceAction(service: str, action: str, params: dict = None) -> str:
    """Interactúa con la suite de Google (Docs, Sheets, Gmail). REQUIERE validación de token."""
    return json.dumps({"__agnux_event": "GOOGLE-WORKSPACE-ACTION", "service": service, "action": action, "params": params or {}})

def openMediaApp(platform: str) -> str:
    """Abre aplicaciones de streaming en modo Kiosco (Chromium aislado)."""
    return json.dumps({"__agnux_event": "OPEN-MEDIA-APP", "platform": platform})

TOOLS_BASE.extend([
    calculateExpression,
    setWallpaper,
    applyCssTheme,
    googleWorkspaceAction,
    openMediaApp
])

# =====================================================================
# 🧠 INSTANCIACIÓN LIMPIA DEL AGENTE CORE DE AGNUX
# El system_message e instructions se inyectan dinámicamente por el
# orquestador en cada llamada (via additional_messages), para poder
# personalizar el contexto de memoria episódica por sesión.
# =====================================================================
agnux_agent = Agent(
    model=objeto_modelo,
    # description e instructions se pasan en tiempo de ejecución desde
    # el orquestador para poder inyectar memoria episódica dinámica.
    description=None,
    instructions=None,
    system_message=None,
    tools=TOOLS_BASE,
    # stream_intermediate_steps debe ser True para que arun() emita
    # ToolCallStartedEvent y ToolCallCompletedEvent al orquestador.
    markdown=False,
)

# =====================================================================
# 🔄 RECARGA COGNITIVA EN CALIENTE (DYNAMIC MODULE HOT-RELOAD)
# Escanea dynamic_tools/, importa y registra las funciones en el agente.
# Normaliza nombres de archivos: guiones medios en disco → guion bajo en símbolo.
# =====================================================================
def recargar_herramientas_dinamicas() -> None:
    """
    Escanea la carpeta dynamic_tools/, compila cada módulo e inyecta
    sus funciones en la lista de herramientas activas del agente.

    Convención de nombres:
      - Archivo en disco: 'global-control-bomba.py'  (guiones medios, OBLIGATORIO)
      - Símbolo Python  : 'global_control_bomba'     (guiones bajos, requerido por Python)

    Si un archivo en disco usa guiones bajos (violación de la regla constitucional),
    se renombra automáticamente antes de importar.
    """
    if DYNAMIC_DIR not in sys.path:
        sys.path.append(DYNAMIC_DIR)

    nuevas_tools = []

    try:
        for archivo in os.listdir(DYNAMIC_DIR):
            if not archivo.endswith(".py"):
                continue
            if archivo in ("__init__.py",):
                continue

            nombre_archivo_sin_ext = archivo.replace(".py", "")

            # ── Normalización constitucional en disco ──────────────────
            if "_" in nombre_archivo_sin_ext:
                nombre_normalizado_disco = nombre_archivo_sin_ext.replace("_", "-")
                ruta_vieja = os.path.join(DYNAMIC_DIR, archivo)
                ruta_nueva = os.path.join(DYNAMIC_DIR, f"{nombre_normalizado_disco}.py")
                os.rename(ruta_vieja, ruta_nueva)
                logger.warning(
                    f"⚠️ [AUTOGÉNESIS] Renombrando '{archivo}' → '{nombre_normalizado_disco}.py' "
                    f"(cumplimiento de regla constitucional de guiones medios)"
                )
                nombre_archivo_sin_ext = nombre_normalizado_disco

            # ── Importación del módulo ─────────────────────────────────
            # El nombre del módulo Python usa guión bajo para el símbolo interno
            nombre_simbolo   = nombre_archivo_sin_ext.replace("-", "_")
            ruta_absoluta    = os.path.join(DYNAMIC_DIR, f"{nombre_archivo_sin_ext}.py")

            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(nombre_simbolo, ruta_absoluta)
                modulo = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(modulo)

                funcion_objeto = getattr(modulo, nombre_simbolo, None)
                if callable(funcion_objeto):
                    nuevas_tools.append(funcion_objeto)
                    logger.info(f"✅ [DYNAMIC TOOLS] '{nombre_archivo_sin_ext}' cargada en el agente.")
                else:
                    logger.warning(
                        f"⚠️ [DYNAMIC TOOLS] Módulo '{nombre_archivo_sin_ext}' no expone "
                        f"una función callable con el nombre '{nombre_simbolo}'. Ignorado."
                    )
            except Exception as e:
                logger.error(f"❌ [DYNAMIC TOOLS] Error importando '{nombre_archivo_sin_ext}': {e}")

        # Actualizar la lista de herramientas del agente: TOOLS_BASE + dinámicas
        agnux_agent.tools = TOOLS_BASE + nuevas_tools
        logger.info(
            f"🔄 [KERNEL] Matriz cognitiva actualizada: "
            f"{len(TOOLS_BASE)} base + {len(nuevas_tools)} dinámicas = "
            f"{len(agnux_agent.tools)} herramientas totales."
        )

    except Exception as e:
        logger.error(f"❌ [KERNEL] Error crítico en recarga dinámica: {e}")