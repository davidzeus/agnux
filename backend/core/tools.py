import json
import os
import re
import subprocess
import webbrowser
from core.config import kernelLogger, dynamicToolsDir
from core.sandbox import evaluarCodigoSandbox

def asegurarPaquete(paquete: str) -> bool:
    try:
        # Check if binary is in path
        subprocess.run(["which", paquete], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        kernelLogger.info(f"🔧 [KERNEL] {paquete} no instalado. Intentando auto-instalación...")
        try:
            # Live environment has passwordless sudo
            subprocess.run(["sudo", "apt-get", "update"], check=False)
            res = subprocess.run(["sudo", "apt-get", "install", "-y", paquete], check=True)
            return res.returncode == 0
        except Exception as e:
            kernelLogger.error(f"Error instalando paquete {paquete}: {e}")
            return False

def openSystemApp(appId: str) -> str:
    """
    Abre una aplicación de sistema nativa (como archivos, calculadora, terminal) en el host.
    Si la aplicación no está instalada, intenta instalarla automáticamente usando apt-get.
    Args:
        appId: Identificador de la aplicación ('archivos', 'calculadora', 'terminal').
    """
    kernelLogger.info(f"🔌 [TOOL] openSystemApp: appId={appId}")
    
    binario = ""
    if appId == "archivos":
        binario = "pcmanfm"
    elif appId == "calculadora":
        binario = "galculator"
    elif appId == "terminal":
        binario = "xterm"
        
    if binario:
        if asegurarPaquete(binario):
            try:
                subprocess.Popen([binario])
            except Exception as e:
                kernelLogger.error(f"Error abriendo aplicación {appId}: {e}")
        else:
            kernelLogger.error(f"No se pudo asegurar que la aplicación {appId} ({binario}) esté instalada.")
            
    return json.dumps({"__agnux_event": "OPEN-SYSTEM-APP", "app-id": appId})

def setWallpaper(imageUrl: str) -> str:
    """
    Establece una imagen como fondo de pantalla de la interfaz.
    Args:
        imageUrl: URL o ruta de la imagen a colocar de fondo.
    """
    kernelLogger.info(f"🔌 [TOOL] setWallpaper: imageUrl={imageUrl}")
    return json.dumps({"__agnux_event": "SET-WALLPAPER", "image-url": imageUrl})

def applyCssTheme(cssCode: str) -> str:
    """
    Aplica una hoja de estilos CSS personalizada sobre la interfaz gráfica completa.
    Args:
        cssCode: El código CSS a aplicar.
    """
    kernelLogger.info(f"🔌 [TOOL] applyCssTheme: cssCode (chars)={len(cssCode)}")
    return json.dumps({"__agnux_event": "SET-THEME", "css-code": cssCode})

def calculateExpression(expression: str) -> str:
    """
    Calcula una expresión matemática compleja devolviendo el resultado numérico exacto.
    Args:
        expression: La ecuación o expresión a resolver (ej: '5 * (10 / 2) + math.sqrt(16)').
    """
    kernelLogger.info(f"🔌 [TOOL] calculateExpression: expression={expression}")
    import math
    try:
        # Safe eval using math symbols
        safeDict = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
        result = eval(expression, {"__builtins__": None}, safeDict)
        return str(result)
    except Exception as e:
        return f"Error evaluando expresión: {e}"

def notificarFrontend(userId: str, mensaje: str, tipo: str = "info") -> str:
    """
    Envía una notificación emergente visual sobre la pantalla del usuario.
    Args:
        userId: ID del usuario destino.
        mensaje: Texto de la notificación.
        tipo: Severidad o tipo ('info', 'warn', 'error', 'success').
    """
    kernelLogger.info(f"🔌 [TOOL] notificarFrontend: userId={userId}, msg={mensaje}")
    return json.dumps({"__agnux_event": "SHOW-NOTIFICATION", "user-id": userId, "message": mensaje, "type": tipo})

def googleWorkspaceAction(actionType: str, payload: str = "") -> str:
    """
    Realiza integraciones de oficina con Google Workspace si la cuenta está autenticada.
    Args:
        actionType: El tipo de acción (ej: 'list-emails', 'create-doc', 'list-calendar').
        payload: Datos de entrada para la operación.
    """
    kernelLogger.info(f"🔌 [TOOL] googleWorkspaceAction: type={actionType}")
    return json.dumps({"__agnux_event": "GOOGLE-WORKSPACE-ACTION", "action": actionType, "payload": payload})

def openWebBrowser(url: str) -> str:
    """
    Abre un navegador web con la URL especificada (por ejemplo, para Netflix o cualquier sitio web).
    Si no hay un navegador instalado, intenta instalar Firefox automáticamente.
    Args:
        url: La dirección web a abrir (ej: 'https://www.netflix.com').
    """
    kernelLogger.info(f"🔌 [TOOL] openWebBrowser: url={url}")
    
    # Lubuntu uses Firefox as standard browser, let's ensure it is installed
    if asegurarPaquete("firefox"):
        try:
            # Launch firefox directly
            subprocess.Popen(["firefox", url])
            return f"Navegador abierto en la URL: {url}"
        except Exception as e:
            kernelLogger.error(f"Error abriendo firefox directamente: {e}. Intentando fallback...")
            
    try:
        webbrowser.open(url)
        return f"Navegador abierto en la URL (fallback): {url}"
    except Exception as e:
        kernelLogger.error(f"Error abriendo navegador: {e}")
        return f"Error abriendo navegador: {e}"

def ejecutarCodigoPython(codigo: str) -> str:
    """
    Ejecuta código Python de manera segura dentro de un contenedor Docker aislado.
    Úsalo para probar lógica, realizar cálculos complejos o evaluar scripts.
    Args:
        codigo: El código Python a ejecutar.
    """
    kernelLogger.info("🔌 [TOOL] ejecutarCodigoPython")
    res = evaluarCodigoSandbox(codigo, lenguaje="python")
    return json.dumps(res, ensure_ascii=False)

def crearArchivo(path: str, contenido: str) -> str:
    """
    Crea o escribe un archivo en el sistema de archivos de AGNUX.
    Puedes usarlo para escribir código de herramientas dinámicas en 'backend/dynamicTools/' o cualquier script.
    Args:
        path: Ruta del archivo (ej: 'dynamicTools/mi_herramienta.py' o 'script.py').
        contenido: El contenido del archivo.
    """
    kernelLogger.info(f"🔌 [TOOL] crearArchivo: path={path}")
    try:
        baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        absPath = os.path.abspath(os.path.join(baseDir, path))
        if not absPath.startswith(baseDir):
            return "Error: Acceso denegado fuera del área del proyecto."
            
        os.makedirs(os.path.dirname(absPath), exist_ok=True)
        with open(absPath, "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"Archivo creado exitosamente en {path}"
    except Exception as e:
        kernelLogger.error(f"Error creando archivo {path}: {e}")
        return f"Error creando archivo: {e}"

def crearDocumento(nombreArchivo: str, contenido: str) -> str:
    """
    Crea un documento de texto con el contenido dado y lo abre inmediatamente
    en un editor gráfico del sistema para que el usuario lo vea y lo edite.
    Úsala cuando el usuario pida redactar, escribir o crear un documento,
    carta, informe, nota o texto: tú generas el contenido completo y esta
    herramienta lo materializa en pantalla. El archivo se guarda en la
    carpeta Documentos del usuario. Si no hay editor instalado, se
    auto-instala uno (mousepad).
    Args:
        nombreArchivo: Nombre del archivo con extensión (ej: 'carta-renuncia.txt', 'informe.md').
        contenido: Texto completo del documento ya redactado.
    """
    kernelLogger.info(f"🔌 [TOOL] crearDocumento: {nombreArchivo} ({len(contenido)} chars)")

    # Sanear nombre: sin rutas, solo el nombre base
    nombreLimpio = os.path.basename(nombreArchivo.strip()) or "documento.txt"
    docsDir = os.path.join(os.path.expanduser("~"), "Documentos")
    os.makedirs(docsDir, exist_ok=True)
    rutaDocumento = os.path.join(docsDir, nombreLimpio)

    try:
        with open(rutaDocumento, "w", encoding="utf-8") as f:
            f.write(contenido)
    except Exception as e:
        kernelLogger.error(f"Error escribiendo documento {rutaDocumento}: {e}")
        return f"Error creando el documento: {e}"

    # Buscar un editor gráfico ya presente en el sistema; si no hay, auto-instalar
    editoresConocidos = ["mousepad", "featherpad", "gedit", "kate", "pluma"]
    editorDisponible = None
    for editor in editoresConocidos:
        if subprocess.run(["which", editor], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL).returncode == 0:
            editorDisponible = editor
            break

    if not editorDisponible and asegurarPaquete("mousepad"):
        editorDisponible = "mousepad"

    if editorDisponible:
        try:
            subprocess.Popen([editorDisponible, rutaDocumento])
            return f"Documento '{nombreLimpio}' creado en {rutaDocumento} y abierto en {editorDisponible}."
        except Exception as e:
            kernelLogger.error(f"Error abriendo editor {editorDisponible}: {e}")

    return f"Documento '{nombreLimpio}' creado en {rutaDocumento} (no se encontró editor gráfico para abrirlo)."

def crearHerramienta(nombreHerramienta: str, codigoPython: str, codigoPrueba: str) -> str:
    """
    Autogenera una nueva herramienta del sistema cuando ninguna herramienta
    existente puede resolver la petición del usuario. Ciclo de autogeneración:
    el código se AUTOPRUEBA primero en el sandbox Docker aislado (sin red) y
    SOLO si la prueba pasa se inyecta en backend/dynamicTools/, quedando
    registrada de inmediato como herramienta invocable en este mismo turno.
    El código debe definir exactamente una función con el mismo nombre que
    nombreHerramienta, con type hints, usando solo la librería estándar de
    Python, y con un docstring que describa qué hace y sus Args (ese docstring
    es lo que te permitirá invocarla luego).
    Args:
        nombreHerramienta: Nombre de la función en camelCase (ej: 'convertirRomanos').
        codigoPython: Código fuente completo que define la función.
        codigoPrueba: Código que invoca la función con casos reales y hace assert de los resultados; debe lanzar excepción si algo falla.
    """
    kernelLogger.info(f"🔌 [TOOL] crearHerramienta: {nombreHerramienta}")

    # 1. Validar el nombre (identificador Python seguro, sin rutas)
    nombreLimpio = nombreHerramienta.strip()
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9]*", nombreLimpio):
        return json.dumps({
            "ok": False,
            "error": f"Nombre inválido '{nombreHerramienta}': usa un identificador camelCase sin espacios ni símbolos."
        }, ensure_ascii=False)

    # 2. El código debe definir la función prometida
    if not re.search(rf"^\s*def\s+{re.escape(nombreLimpio)}\s*\(", codigoPython, re.MULTILINE):
        return json.dumps({
            "ok": False,
            "error": f"El código no define la función '{nombreLimpio}'. Define exactamente 'def {nombreLimpio}(...)'."
        }, ensure_ascii=False)

    # 3. Autoprueba en el sandbox aislado: definición + casos de prueba
    codigoCompleto = f"{codigoPython}\n\n# --- AUTOPRUEBA DEL KERNEL ---\n{codigoPrueba}\nprint('AGNUX-SELFTEST-OK')\n"
    resultado = evaluarCodigoSandbox(codigoCompleto, lenguaje="python")

    if not resultado.get("ok") or "AGNUX-SELFTEST-OK" not in resultado.get("output", ""):
        kernelLogger.warning(f"⚠️ [SELF-FORGE] '{nombreLimpio}' NO pasó la autoprueba. Rechazada.")
        return json.dumps({
            "ok": False,
            "error": "La autoprueba en el sandbox falló. Corrige el código o la prueba y reintenta.",
            "sandboxOutput": resultado.get("output", ""),
            "exitCode": resultado.get("exitCode", -1)
        }, ensure_ascii=False)

    # 4. Inyección: persistir la herramienta aprobada en dynamicTools/
    rutaHerramienta = os.path.join(dynamicToolsDir, f"{nombreLimpio}.py")
    try:
        with open(rutaHerramienta, "w", encoding="utf-8") as f:
            f.write(codigoPython)
    except Exception as e:
        kernelLogger.error(f"Error inyectando herramienta {nombreLimpio}: {e}")
        return json.dumps({"ok": False, "error": f"Autoprueba OK pero falló la inyección: {e}"}, ensure_ascii=False)

    kernelLogger.info(
        f"⚒️ [SELF-FORGE] Herramienta '{nombreLimpio}' aprobada en sandbox "
        f"({resultado.get('executionTimeMs')}ms) e inyectada en {rutaHerramienta}"
    )
    return json.dumps({
        "ok": True,
        "mensaje": f"Herramienta '{nombreLimpio}' autoprobada en sandbox e inyectada al sistema. Ya está disponible para invocarse.",
        "sandboxOutput": resultado.get("output", ""),
        "executionTimeMs": resultado.get("executionTimeMs", 0),
        "ruta": f"dynamicTools/{nombreLimpio}.py"
    }, ensure_ascii=False)

def crearVentana(titulo: str, htmlContenido: str, ventanaId: str = "") -> str:
    """
    Materializa una ventana flotante en el escritorio del usuario con contenido HTML libre.
    Úsala siempre que el usuario pida un panel, dashboard, tabla, tarjeta, lista visual,
    formulario, reporte o cualquier interfaz que se exprese mejor de forma visual que como texto.
    El HTML se renderiza dentro de una ventana de cristal nativa del shell: puedes usar
    etiquetas estándar (div, h1-h4, p, table, ul, progress, svg...) y estilos inline.
    Las variables CSS del sistema están disponibles para integrarte al tema activo:
    var(--agnux-accent), var(--agnux-accent-2), var(--agnux-text-primary),
    var(--agnux-text-secondary), var(--agnux-panel-border).
    INTERACTIVIDAD: agrega data-intent="petición en lenguaje natural" a botones,
    filas o tarjetas; al hacer click, ese intent se te enviará como si el usuario
    lo hubiera escrito, y podrás responder o actualizar esta ventana (mismo
    ventanaId). Los placeholders {campo} dentro del data-intent se reemplazan
    con el valor del input/select/textarea de la ventana cuyo name o id sea
    'campo' (ej: <input name="monto"> y
    <button data-intent="convertir {monto} dólares a euros">Convertir</button>).
    No incluyas <html>, <head>, <body> ni <script>; solo el fragmento del cuerpo.
    Args:
        titulo: Título visible en la barra de la ventana.
        htmlContenido: Fragmento HTML libre a renderizar dentro de la ventana.
        ventanaId: Identificador opcional en kebab-case; si ya existe una ventana con ese id, se actualiza su contenido en vivo.
    """
    kernelLogger.info(f"🔌 [TOOL] crearVentana: titulo={titulo}, html (chars)={len(htmlContenido)}")
    return json.dumps({
        "__agnux_event": "CREATE-WINDOW",
        "window-id": ventanaId,
        "title": titulo,
        "html": htmlContenido
    }, ensure_ascii=False)

def useSkill(skillName: str) -> str:
    """
    Recupera y activa una habilidad (skill) del framework de Superpowers.
    Se debe invocar cuando se inicia o se requiere disciplina en una tarea de diseño, planificación, desarrollo (TDD), depuración o verificación.
    Args:
        skillName: Nombre de la habilidad (ej: 'brainstorming', 'writing-plans', 'executing-plans', 'test-driven-development', 'systematic-debugging', 'verification-before-completion').
    """
    kernelLogger.info(f"🔌 [TOOL] useSkill: skillName={skillName}")
    
    # Path inside backend
    baseDir = os.path.dirname(os.path.abspath(__file__))
    skillPath = os.path.join(baseDir, "skills", skillName, "SKILL.md")
    
    if not os.path.exists(skillPath):
        return f"Error: La habilidad '{skillName}' no existe en el sistema."
        
    try:
        with open(skillPath, "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error leyendo la habilidad '{skillName}': {e}"
