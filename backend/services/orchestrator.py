import os
import json
import asyncio
from datetime import datetime
from agno.agent import Agent
from qdrant_client.models import Filter, FieldCondition, MatchValue

from core.config import (
    iaProvider,
    agnuxActiveModel,
    agnuxCoderModel,
    geminiApiKey,
    openaiApiKey,
    ollamaHost,
    kernelLogger,
    baseDir,
    aiStats
)
from core.memory import (
    qdrantClient,
    coleccionMemoria,
    guardarRecuerdoQdrant,
    buscarRecuerdosQdrant,
    generarVectorTexto
)
from core.database import (
    guardarMensajeChat,
    obtenerMensajesChat,
    guardarPreferencia,
    obtenerPreferencia
)
from core.tools import (
    openSystemApp,
    setWallpaper,
    applyCssTheme,
    calculateExpression,
    notificarFrontend,
    googleWorkspaceAction,
    useSkill,
    openWebBrowser,
    ejecutarCodigoPython,
    crearArchivo,
    crearVentana,
    crearDocumento,
    crearHerramienta
)
from core.dynamicToolsLoader import cargarHerramientasDinamicas

# Active fallbacks memory
pendingFallbacks = {}

# Mutex to secure inference bus
ollamaBusLock = asyncio.Lock()

# Standard tools list
agnuxTools = [
    openSystemApp,
    setWallpaper,
    applyCssTheme,
    calculateExpression,
    notificarFrontend,
    googleWorkspaceAction,
    useSkill,
    openWebBrowser,
    ejecutarCodigoPython,
    crearArchivo,
    crearVentana,
    crearDocumento,
    crearHerramienta
]

def registrarHerramientasDinamicas():
    """
    Fusiona las herramientas autogeneradas (dynamicTools/) en el arsenal del
    agente. Se llama al arrancar y cada vez que crearHerramienta inyecta una
    nueva, para que quede invocable sin reiniciar el Kernel.
    """
    indicePorNombre = {t.__name__: i for i, t in enumerate(agnuxTools)}
    for funcion in cargarHerramientasDinamicas():
        if funcion.__name__ in indicePorNombre:
            agnuxTools[indicePorNombre[funcion.__name__]] = funcion
        else:
            agnuxTools.append(funcion)
            indicePorNombre[funcion.__name__] = len(agnuxTools) - 1

# Carga inicial de herramientas autogeneradas en arranque del Kernel
registrarHerramientasDinamicas()

def normalizarId(rawId: str) -> str:
    return rawId.strip().lower().replace("_", "-")

def instanciarModelo(provider: str, modelId: str):
    if provider == "gemini" and geminiApiKey:
        from agno.models.google import Gemini
        return Gemini(id=modelId, api_key=geminiApiKey)
    elif provider == "openai" and openaiApiKey:
        from agno.models.openai import OpenAIChat
        return OpenAIChat(id=modelId, api_key=openaiApiKey)
    else:
        from agno.models.ollama import Ollama
        return Ollama(id=modelId, host=ollamaHost)

def instanciarAgente(systemMessage: str = None) -> Agent:
    modelObject = instanciarModelo(iaProvider, agnuxActiveModel)
    return Agent(
        model=modelObject,
        description="Core cognitive kernel of AGNUX OS.",
        system_message=systemMessage,
        tools=agnuxTools,
        markdown=False
    )

def modificarEnv(provider: str, numGpu: str, model: str = None):
    envPath = os.path.join(baseDir, ".env")
    if not os.path.exists(envPath):
        envPath = os.path.join(os.path.dirname(baseDir), ".env")
    if not os.path.exists(envPath):
        return
        
    with open(envPath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    newLines = []
    foundProvider = False
    foundGpu = False
    foundActiveModel = False
    foundCoderModel = False
    
    for line in lines:
        cleanLine = line.strip()
        if cleanLine.startswith("iaProvider="):
            newLines.append(f"iaProvider={provider}\n")
            foundProvider = True
        elif cleanLine.startswith("numGpu="):
            newLines.append(f"numGpu={numGpu}\n")
            foundGpu = True
        elif cleanLine.startswith("agnuxActiveModel="):
            if model:
                newLines.append(f"agnuxActiveModel={model}\n")
            else:
                newLines.append(line)
            foundActiveModel = True
        elif cleanLine.startswith("agnuxCoderModel="):
            if model:
                newLines.append(f"agnuxCoderModel={model}\n")
            else:
                newLines.append(line)
            foundCoderModel = True
        else:
            newLines.append(line)
            
    if not foundProvider:
        newLines.append(f"iaProvider={provider}\n")
    if not foundGpu:
        newLines.append(f"numGpu={numGpu}\n")
    if model and not foundActiveModel:
        newLines.append(f"agnuxActiveModel={model}\n")
    if model and not foundCoderModel:
        newLines.append(f"agnuxCoderModel={model}\n")
        
    with open(envPath, "w", encoding="utf-8") as f:
        f.writelines(newLines)
    kernelLogger.info(f"💾 .env actualizado: iaProvider={provider}, numGpu={numGpu}, model={model}")

def obtenerPromptSuperpowers() -> str:
    try:
        baseDir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(baseDir, "..", "core", "skills", "using-superpowers", "SKILL.md")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"\n<EXTREMELY_IMPORTANT>\nYou have superpowers.\n\n**Below is the full content of your 'superpowers:using-superpowers' skill - your introduction to using skills. For all other skills, use the 'useSkill' tool:**\n\n{content}\n</EXTREMELY_IMPORTANT>\n"
    except Exception as e:
        kernelLogger.error(f"Error cargando using-superpowers skill: {e}")
    return ""

async def _despacharSystemTool(toolName: str, toolArgs: dict, userId: str) -> tuple[str, str]:
    # Custom dispatcher for static system actions
    try:
        if toolName == "openSystemApp":
            res = openSystemApp(toolArgs.get("appId", ""))
            return f"event: OPEN-SYSTEM-APP\ndata: {res}\n\n", "Aplicación iniciada."
        elif toolName == "setWallpaper":
            res = setWallpaper(toolArgs.get("imageUrl", ""))
            return f"event: SET-WALLPAPER\ndata: {res}\n\n", "Fondo de pantalla actualizado."
        elif toolName == "applyCssTheme":
            cssCode = toolArgs.get("cssCode", "")
            res = applyCssTheme(cssCode)
            return f"event: SET-THEME\ndata: {res}\n\n", "Tema visual aplicado."
        elif toolName == "calculateExpression":
            res = calculateExpression(toolArgs.get("expression", ""))
            return "", f"Ecuación resuelta: {res}"
        elif toolName == "notificarFrontend":
            res = notificarFrontend(userId, toolArgs.get("mensaje", ""), toolArgs.get("tipo", "info"))
            return f"event: SHOW-NOTIFICATION\ndata: {res}\n\n", "Notificación despachada."
        elif toolName == "googleWorkspaceAction":
            res = googleWorkspaceAction(toolArgs.get("actionType", ""), toolArgs.get("payload", ""))
            return f"event: GOOGLE-WORKSPACE-ACTION\ndata: {res}\n\n", "Acción de Workspace completada."
        elif toolName == "useSkill":
            skillName = toolArgs.get("skillName", "")
            payloadEvent = json.dumps({"event": "ACTIVATE-SKILL", "skill": skillName})
            return f"event: ACTIVATE-SKILL\ndata: {payloadEvent}\n\n", f"Habilidad '{skillName}' cargada y activa."
        elif toolName == "openWebBrowser":
            url = toolArgs.get("url", "")
            res = openWebBrowser(url)
            payloadEvent = json.dumps({"__agnux_event": "SHOW-NOTIFICATION", "user-id": userId, "message": f"Abriendo navegador en {url}", "type": "info"})
            return f"event: SHOW-NOTIFICATION\ndata: {payloadEvent}\n\n", f"Navegador abierto en {url}."
        elif toolName == "ejecutarCodigoPython":
            codigo = toolArgs.get("codigo", "")
            res = ejecutarCodigoPython(codigo)
            return "", res
        elif toolName == "crearArchivo":
            path = toolArgs.get("path", "")
            contenido = toolArgs.get("contenido", "")
            res = crearArchivo(path, contenido)
            return "", res
        elif toolName == "crearVentana":
            res = crearVentana(
                toolArgs.get("titulo", ""),
                toolArgs.get("htmlContenido", ""),
                toolArgs.get("ventanaId", "")
            )
            return f"event: CREATE-WINDOW\ndata: {res}\n\n", "Ventana materializada en el escritorio."
        elif toolName == "crearHerramienta":
            # El agente ya ejecutó la tool (sandbox + inyección); aquí solo
            # recargamos el arsenal para que la herramienta nueva sea
            # invocable de inmediato. No se re-ejecuta la autoprueba.
            registrarHerramientasDinamicas()
            return "", ""
    except Exception as e:
        kernelLogger.error(f"Error despachando tool {toolName}: {e}")
    return "", ""

def clasificadorCpuMini(promptText: str) -> dict | None:
    """
    Evalúa localmente en CPU si el prompt puede ser resuelto por una tarea simple / mini 
    para ahorrar tokens antes de recurrir a modelos de razonamiento (Gemini u Ollama).
    """
    cleanText = promptText.lower().strip()
    
    # 1. Simple Calculator
    import re
    # Match basic arithmetic like: 2 + 2, 50 * 3, 100 / 4
    if re.match(r'^[\d+\-*/\(\)\s.]+$', cleanText) and any(op in cleanText for op in ["+", "-", "*", "/"]):
        return {
            "tool": "calculateExpression",
            "args": {"expression": cleanText}
        }
        
    # 2. Open System Apps
    if "abrir" in cleanText or "ejecutar" in cleanText or "lanzar" in cleanText:
        if any(term in cleanText for term in ["archivos", "file manager", "pcmanfm", "explorer"]):
            return {"tool": "openSystemApp", "args": {"appId": "archivos"}}
        if any(term in cleanText for term in ["calculadora", "galculator", "calculator"]):
            return {"tool": "openSystemApp", "args": {"appId": "calculadora"}}
        if any(term in cleanText for term in ["terminal", "consola", "xterm", "bash"]):
            return {"tool": "openSystemApp", "args": {"appId": "terminal"}}
            
        # 3. Open browser urls
        urlMatch = re.search(r'(https?://\S+|www\.\S+|\w+\.(com|org|net|io|edu|tv|es|co)\S*)', cleanText)
        if urlMatch:
            url = urlMatch.group(0)
            if not url.startswith("http"):
                url = "https://" + url
            return {"tool": "openWebBrowser", "args": {"url": url}}
        elif "netflix" in cleanText:
            return {"tool": "openWebBrowser", "args": {"url": "https://www.netflix.com"}}
        elif "youtube" in cleanText:
            return {"tool": "openWebBrowser", "args": {"url": "https://www.youtube.com"}}
        elif "google" in cleanText:
            return {"tool": "openWebBrowser", "args": {"url": "https://www.google.com"}}
        elif "navegador" in cleanText:
            return {"tool": "openWebBrowser", "args": {"url": "https://www.google.com"}}
            
    # 4. Set Wallpaper
    if any(term in cleanText for term in ["wallpaper", "fondo de pantalla"]):
        urlMatch = re.search(r'(https?://\S+)', cleanText)
        if urlMatch:
            return {"tool": "setWallpaper", "args": {"imageUrl": urlMatch.group(0)}}
            
    return None

async def procesarGeneradorEventos(payload, isGoogleConnected: bool):
    userIdNorm = normalizarId(payload.user_id)
    terminalIdNorm = normalizarId(payload.terminal_id)
    promptText = payload.prompt.strip()
    
    kernelLogger.info(f"📥 [ORCHESTRATOR] procesarGeneradorEventos: user={userIdNorm}, prompt='{promptText}'")
    
    try:
        # Intercept LLM provider switch requests
        lowercasePrompt = promptText.lower()
        esCambioProveedor = False
        nuevoProveedor = None
        nuevoModelo = None
        numGpu = "1"
        
        # Check for local/ollama
        if ("modo local" in lowercasePrompt or "ollama" in lowercasePrompt or "usar local" in lowercasePrompt or "switch to local" in lowercasePrompt) and not ("gemini" in lowercasePrompt):
            esCambioProveedor = True
            nuevoProveedor = "local"
            nuevoModelo = "qwen2.5-coder:7b"
        # Check for gemini
        elif ("gemini" in lowercasePrompt or "usar gemini" in lowercasePrompt or "switch to gemini" in lowercasePrompt) and not ("ollama" in lowercasePrompt or "local" in lowercasePrompt):
            esCambioProveedor = True
            nuevoProveedor = "gemini"
            nuevoModelo = "gemini-2.5-flash"
            
        if esCambioProveedor:
            import core.config
            import services.orchestrator
            
            # Update configuration in memory
            core.config.iaProvider = nuevoProveedor
            core.config.agnuxActiveModel = nuevoModelo
            core.config.agnuxCoderModel = nuevoModelo
            
            services.orchestrator.iaProvider = nuevoProveedor
            services.orchestrator.agnuxActiveModel = nuevoModelo
            services.orchestrator.agnuxCoderModel = nuevoModelo
            
            # Update globally tracked telemetry stats
            core.config.aiStats["provider"] = nuevoProveedor
            core.config.aiStats["model"] = nuevoModelo
            core.config.aiStats["status"] = "Online"
            core.config.aiStats["lastErrorMessage"] = ""
            
            # Save to .env
            modificarEnv(nuevoProveedor, numGpu, nuevoModelo)
            
            # Notify frontend immediately
            msgExito = f"✓ Cambiado el proveedor de IA a **{nuevoProveedor.upper()}** (Modelo: `{nuevoModelo}`) exitosamente."
            yield json.dumps({"event": "TEXT-CHUNK", "content": msgExito}) + "\n"
            
            # Save message to database history
            guardarMensajeChat(userIdNorm, terminalIdNorm, "user", promptText)
            guardarMensajeChat(userIdNorm, terminalIdNorm, "kernel", msgExito)
            return

        # Intercept via clasificadorCpuMini to minimize token usage
        decisionCpu = clasificadorCpuMini(promptText)
        if decisionCpu:
            tName = decisionCpu["tool"]
            tArgs = decisionCpu["args"]
            
            kernelLogger.info(f"⚡ [CPU MINI ROUTER] Prompt '{promptText}' resuelto localmente en CPU con 0 tokens.")
            yield json.dumps({
                "event": "TOOL-EXECUTE",
                "message": f"Ejecutando herramienta local (CPU): {tName}",
                "tool-name": tName
            }) + "\n"
            
            # Execute tool
            sseFrame, feedback = await _despacharSystemTool(tName, tArgs, userIdNorm)
            if sseFrame:
                yield sseFrame
            
            # Yield tool result
            yield json.dumps({"event": "TOOL-RESULT", "data": feedback}) + "\n"
            
            # Yield text chunk response
            responseMsg = f"✓ Comando de sistema ejecutado con éxito: {feedback}"
            yield json.dumps({"event": "TEXT-CHUNK", "content": responseMsg}) + "\n"
            
            # Save to database
            guardarMensajeChat(userIdNorm, terminalIdNorm, "user", promptText)
            guardarMensajeChat(userIdNorm, terminalIdNorm, "kernel", responseMsg)
            return

        # Check queue
        if ollamaBusLock.locked():
            yield json.dumps({
                "event": "QUEUE-WAIT",
                "message": "Servidor ocupado. Solicitud en cola del Kernel..."
            }) + "\n"
            
        async with ollamaBusLock:
            # 1. Fallback menu choices handler
            if userIdNorm in pendingFallbacks:
                decision = promptText.lower()
                isValid = decision in ["1", "memoria", "qdrant", "2", "cpu", "ollama cpu", "3", "gpu", "ollama gpu", "4", "fallback"]
                
                if isValid:
                    pendingData = pendingFallbacks.pop(userIdNorm)
                    originalPrompt = pendingData["prompt"]
                    
                    if decision in ["1", "memoria", "qdrant"]:
                        yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '🔍 [Qdrant] Recuperando tema semántico de tu historial...'}, ensure_ascii=False)}\n\n"
                        try:
                            vectorValue = generarVectorTexto(originalPrompt)
                            searchResults = await qdrantClient.query_points(
                                collection_name=coleccionMemoria,
                                query=vectorValue,
                                query_filter=Filter(
                                    must=[
                                        FieldCondition(key="userId", match=MatchValue(value=userIdNorm)),
                                        FieldCondition(key="tipo", match=MatchValue(value="theme_css"))
                                    ]
                                ),
                                limit=1
                            )
                            if searchResults.points:
                                cssCode = searchResults.points[0].payload.get("cssCode")
                                if cssCode:
                                    yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '✓ Tema similar recuperado con éxito. Aplicando...'}, ensure_ascii=False)}\n\n"
                                    yield f"event: SET-THEME\ndata: {json.dumps({'event': 'SET-THEME', 'css-code': cssCode}, ensure_ascii=False)}\n\n"
                                    return
                            yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '⚠️ No se encontraron temas guardados. Usando fallback estático...'}, ensure_ascii=False)}\n\n"
                        except Exception as e:
                            yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': f'⚠️ Error consultando Qdrant: {e}. Usando fallback...'}, ensure_ascii=False)}\n\n"
                        
                        yield f"event: SET-THEME\ndata: {json.dumps({'event': 'SET-THEME', 'css-code': pendingData['fallbackCss']}, ensure_ascii=False)}\n\n"
                        return
                        
                    elif decision in ["2", "cpu", "ollama cpu"]:
                        yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '⚙️ [Kernel] Configurando proveedor a Local (Ollama CPU)...'}, ensure_ascii=False)}\n\n"
                        modificarEnv("local", "0")
                        yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '✓ Guardado. Por favor reinicia el servicio del backend para aplicar.'}, ensure_ascii=False)}\n\n"
                        return
                        
                    elif decision in ["3", "gpu", "ollama gpu"]:
                        yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '⚙️ [Kernel] Configurando proveedor a Local (Ollama GPU)...'}, ensure_ascii=False)}\n\n"
                        modificarEnv("local", "1")
                        yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '✓ Guardado. Por favor reinicia el servicio del backend para aplicar.'}, ensure_ascii=False)}\n\n"
                        return
                        
                    else:
                        yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': '🎨 [Fallback] Aplicando tema estático predefinido...'}, ensure_ascii=False)}\n\n"
                        yield f"event: SET-THEME\ndata: {json.dumps({'event': 'SET-THEME', 'css-code': pendingData['fallbackCss']}, ensure_ascii=False)}\n\n"
                        return
                else:
                    pendingFallbacks.pop(userIdNorm, None)
                    kernelLogger.info(f"🔄 Menú cancelado para '{userIdNorm}'. Procesando como nueva solicitud.")

            # 2. Main execution flow
            yield json.dumps({
                "event": "ROUTER-START",
                "message": "Inicializando Router Semántico de AGNUX..."
            }) + "\n"
            
            # Search available schemas
            activeSchemas = []
            for tool in agnuxTools:
                scoreVal = 0.8 # Simulated semantic match
                yield json.dumps({"event": "ROUTER-SCORE", "tool": tool.__name__, "score": scoreVal}) + "\n"
                activeSchemas.append(tool)
                
            # Retrieve episodic memories (Context vector search)
            memoriesText = ""
            memories = await buscarRecuerdosQdrant(userIdNorm, promptText, limit=3)
            if memories:
                memoriesText = "\n\n## RECUERDOS EPISÓDICOS RELEVANTES:\n" + "\n".join([f"- {m['contenido']}" for m in memories if m['score'] > 0.4])
                
            # Retrieve session SQLite history
            chatHistory = obtenerMensajesChat(userIdNorm, terminalIdNorm, limit=6)
            historyText = ""
            if chatHistory:
                historyText = "\n\n## HISTORIAL RECIENTE DE CONVERSACIÓN:\n" + "\n".join([f"{m['role']}: {m['content']}" for m in chatHistory])
                
            # 3. Check for Style Customization (Style Engine Agent)
            styleKeywords = ["tema", "estilo", "css", "color", "fondo", "diseño", "theme", "style", "customizar", "personalizar"]
            isStyleRequest = any(kw in promptText.lower() for kw in styleKeywords)
            
            if isStyleRequest:
                yield json.dumps({"event": "TOOL-EXECUTE", "message": "🎨 Generando tema CSS personalizado...", "tool-name": "style-engine"}) + "\n"
                
                # Setup Style System Prompt
                styleTemplate = """:root {
  --agnux-bg-color: [FILL_COLOR];
  --agnux-text-primary: [FILL_COLOR];
  --agnux-text-secondary: [FILL_COLOR];
  --agnux-accent: [FILL_COLOR];
  --agnux-accent-glow: [FILL_RGBA];
  --agnux-accent-dim: [FILL_COLOR];
  --agnux-accent-border: [FILL_COLOR];
  --agnux-panel-bg: [FILL_RGBA];
  --agnux-panel-solid: [FILL_COLOR];
  --agnux-panel-border: [FILL_COLOR];
  --agnux-panel-blur: blur(25px);
  --agnux-font-main: 'Outfit', sans-serif;
  --agnux-font-clock: 'Inter', sans-serif;
}"""
                stylePrompt = f"""
                You are a CSS Web Designer. The user requested: '{promptText}'.
                Generate a custom glassy theme matching their request. Keep it clean, elegant, and minimal like iOS/macOS.
                Fill in all placeholders in this template:
                {styleTemplate}
                Return ONLY the completed :root {{ ... }} block. No markdown, no fences, no explanation.
                """
                
                cssFinal = None
                try:
                    styleModelObject = instanciarModelo(iaProvider, agnuxCoderModel)
                    styleAgent = Agent(model=styleModelObject, system_message="Output pure CSS rules only.", markdown=False)
                    response = styleAgent.run(stylePrompt)
                    cssRaw = response.content if hasattr(response, "content") else str(response)
                    
                    # Clean markdown fences
                    cssClean = cssRaw.strip()
                    for fence in ["```css", "```css\n", "```\n", "```", "`"]:
                        cssClean = cssClean.replace(fence, "")
                    cssClean = cssClean.strip()
                    
                    if ":root" in cssClean and "--agnux-bg-color" in cssClean:
                        cssFinal = cssClean
                        aiStats["status"] = "Online"
                        aiStats["lastErrorMessage"] = ""
                except Exception as e:
                    kernelLogger.error(f"❌ [STYLE-ENGINE] Error en el modelo: {e}")
                    cssFinal = None
                    errStr = str(e)
                    if any(kw in errStr.lower() for kw in ["quota", "limit", "429", "exceeded", "exhausted"]):
                        aiStats["status"] = "Quota Exceeded"
                    else:
                        aiStats["status"] = "Error"
                    aiStats["lastErrorMessage"] = errStr
                    
                if cssFinal:
                    kernelLogger.info(f"🎨 [STYLE-ENGINE] Nuevo CSS sintetizado:\n{cssFinal[:200]}")
                    yield f"event: SET-THEME\ndata: {json.dumps({'event': 'SET-THEME', 'css-code': cssFinal}, ensure_ascii=False)}\n\n"
                    
                    # Persist theme vectors to Qdrant & history to SQLite
                    await guardarRecuerdoQdrant(userIdNorm, "theme_css", f"Estilo: {promptText}", {"cssCode": cssFinal})
                    guardarMensajeChat(userIdNorm, terminalIdNorm, "user", promptText)
                    guardarMensajeChat(userIdNorm, terminalIdNorm, "kernel", f"✓ Estilo aplicado: {promptText}")
                    return
                else:
                    # Trigger fallback warning
                    defaultCss = """:root {
  --agnux-bg-color: #f6f6f9;
  --agnux-text-primary: #1d1d1f;
  --agnux-text-secondary: #86868b;
  --agnux-accent: #0071e3;
  --agnux-accent-glow: rgba(0, 113, 227, 0.2);
  --agnux-accent-dim: #005bb7;
  --agnux-accent-border: #d2d2d7;
  --agnux-panel-bg: rgba(255, 255, 255, 0.7);
  --agnux-panel-solid: #ffffff;
  --agnux-panel-border: rgba(0, 0, 0, 0.08);
  --agnux-panel-blur: blur(25px);
  --agnux-font-main: 'Outfit', sans-serif;
  --agnux-font-clock: 'Inter', sans-serif;
}"""
                    pendingFallbacks[userIdNorm] = {
                        "prompt": promptText,
                        "fallbackCss": defaultCss
                    }
                    warningText = (
                        "⚠️ [ALERTA DE QUOTA] El proveedor de IA no pudo generar el estilo (Excedido o 404).\n"
                        "Por favor selecciona una opción para proceder:\n"
                        "1. [MEMORIA] Recuperar el tema más parecido guardado en Qdrant.\n"
                        "2. [CPU] Cambiar a proveedor local Ollama en modo CPU.\n"
                        "3. [GPU] Cambiar a proveedor local Ollama en modo GPU.\n"
                        "4. [FALLBACK] Usar el tema minimalista por defecto de iOS (Claro)."
                    )
                    yield f"event: TEXT-CHUNK\ndata: {json.dumps({'content': warningText}, ensure_ascii=False)}\n\n"
                    return

            # 4. Standard conversational flow
            superpowersPrompt = obtenerPromptSuperpowers()
            systemPrompt = f"""
            You are the Core Kernel of AGNUX OS: the user states an intent in natural
            language and YOU solve it end to end, acting on the real system.
            Ensure all user IDs and properties use kebab-case.
            All Python code and variables you write/expose must strictly use camelCase.

            RESOLUTION STRATEGY (in order):
            1. If an available tool solves the intent, invoke it directly. Examples:
               navigate the web -> openWebBrowser (auto-installs a browser if missing);
               write/redact a document -> generate the full text yourself and pass it
               to crearDocumento (saves it and opens it in a graphical editor);
               open host apps -> openSystemApp; run/verify code -> ejecutarCodigoPython.
            2. For panels, dashboards, tables, reports, forms or any visual answer,
               materialize a window with 'crearVentana' passing free HTML (no <script>);
               reuse the same ventanaId to live-update a window you already created.
            3. If NO tool can solve the intent, FORGE ONE: call 'crearHerramienta' with
               the function code plus assert-based test cases. It self-tests in the
               isolated Docker sandbox and, only if the tests pass, injects the tool
               into the system, making it available immediately — then invoke it to
               finish the task. If the self-test fails, fix the code and retry.
            Prefer solving over explaining: the user wants the result, not instructions.
            
            Available tools:
            {json.dumps([t.__name__ for t in agnuxTools])}
            {memoriesText}
            {historyText}
            
            {superpowersPrompt}
            """
            
            agentObject = instanciarAgente(systemPrompt)
            completeResponseText = ""
            lastToolName = None
            lastToolArgs = {}
            toolResultData = ""
            
            try:
                # Streaming Agent run
                async for event in agentObject.arun(
                    promptText,
                    stream=True,
                    stream_intermediate_steps=True,
                    session_id=f"{terminalIdNorm}--{userIdNorm}",
                    additional_context={"terminal-id": terminalIdNorm, "user-id": userIdNorm}
                ):
                    eventType = str(getattr(event, "event", getattr(event, "type", "")))
                    
                    # Tool Started
                    if "tool_call_started" in eventType.lower():
                        toolsList = getattr(event, "tools", [])
                        if toolsList:
                            tData = toolsList[0]
                            tName = getattr(tData, "tool_name", getattr(tData, "name", ""))
                            tArgs = getattr(tData, "tool_args", getattr(tData, "arguments", {}))
                            lastToolName = tName
                            lastToolArgs = tArgs
                            
                            yield json.dumps({
                                "event": "TOOL-EXECUTE",
                                "message": f"Ejecutando herramienta: {lastToolName}",
                                "tool-name": lastToolName
                            }) + "\n"
                            
                    # Tool Completed
                    elif "tool_call_completed" in eventType.lower():
                        toolsList = getattr(event, "tools", [])
                        if toolsList:
                            tData = toolsList[0]
                            tResult = getattr(tData, "content", getattr(tData, "result", ""))
                            
                            # Custom actions dispatcher
                            sseFrame, feedback = await _despacharSystemTool(lastToolName, lastToolArgs, userIdNorm)
                            if sseFrame:
                                yield sseFrame
                                toolResultData = feedback
                            else:
                                toolResultData = str(tResult)
                                
                            yield json.dumps({"event": "TOOL-RESULT", "data": toolResultData}) + "\n"
                            
                    # Raw response text chunk
                    else:
                        chunkContent = getattr(event, "content", "")
                        if chunkContent and isinstance(chunkContent, str):
                            completeResponseText += chunkContent
                            yield json.dumps({"event": "TEXT-CHUNK", "content": chunkContent}) + "\n"
                            
            except Exception as eAgent:
                kernelLogger.error(f"❌ [AGNO ENGINE] Error en stream: {eAgent}")
                errStr = str(eAgent)
                if any(kw in errStr.lower() for kw in ["quota", "limit", "429", "exceeded", "exhausted"]):
                    aiStats["status"] = "Quota Exceeded"
                else:
                    aiStats["status"] = "Error"
                aiStats["lastErrorMessage"] = errStr
                yield json.dumps({"event": "ERROR", "message": f"Error en motor: {eAgent}"}) + "\n"
                return
                
            # Success - update metrics
            aiStats["status"] = "Online"
            aiStats["lastErrorMessage"] = ""
            try:
                promptWords = len(promptText.split())
                responseWords = len(completeResponseText.split())
                promptTokens = int(promptWords * 1.33) + 120
                responseTokens = int(responseWords * 1.33)
                aiStats["tokensPrompt"] += promptTokens
                aiStats["tokensResponse"] += responseTokens
                aiStats["totalTokens"] += (promptTokens + responseTokens)
            except Exception as eMetric:
                kernelLogger.error(f"Error calculating metrics: {eMetric}")
                
            # Save conversations
            if completeResponseText.strip():
                guardarMensajeChat(userIdNorm, terminalIdNorm, "user", promptText)
                guardarMensajeChat(userIdNorm, terminalIdNorm, "kernel", completeResponseText.strip())
                
                # Chat context is maintained in console; no duplicate popup windows are forced open.
                
                # Save semantic trace to Qdrant
                semanticLog = f"Usuario: {promptText}\nKernel: {completeResponseText.strip()}"
                asyncio.create_task(guardarRecuerdoQdrant(userIdNorm, "chat-interaction", semanticLog))
                
    finally:
        kernelLogger.info("🔌 [ORCHESTRATOR] Conclusión del generador de eventos.")
