import json
import os
import subprocess
import webbrowser
from core.config import kernelLogger
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
