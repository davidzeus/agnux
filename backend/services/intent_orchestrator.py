# services/intent_orchestrator.py
# =====================================================================
# 🧠 AGNUX OS — ORQUESTADOR DE INTENCIONES (Motor Agno Nativo)
# =====================================================================
# REGLA CONSTITUCIONAL: Está TAXATIVAMENTE PROHIBIDO el uso de guiones
# bajos ('_') en identificadores de usuario, nombre de terminal o
# variables de contexto del host. Usar SIEMPRE guiones medios ('-').
# =====================================================================
import os
import json
import asyncio

from agno.agent import Agent
from qdrant_client.models import Filter, FieldCondition, MatchValue

from core.config import logger, BASE_DIR
from core.memory import (
    OLLAMA_BUS_LOCK,
    CACHE_VECTORS,
    qdrant_client,
    COLECCION_MEMORIA,
    generar_vector_texto,
    guardar_recuerdo_qdrant,
)
from schemas.models import TaskbarPrompt
from services.tools_service import SYSTEM_TOOLS, autogenerar_nueva_tool

from agent_core import agnux_agent, recargar_herramientas_dinamicas, TOOLS_BASE

# Memoria a corto plazo en RAM
SESSION_HISTORY = {}


# =====================================================================
# 🔑 NORMALIZACIÓN CONSTITUCIONAL DE IDENTIFICADORES
# Convierte cualquier identificador con guiones bajos a guiones medios.
# =====================================================================
def _normalizar_id(valor: str) -> str:
    """Normaliza un identificador reemplazando guiones bajos por guiones medios."""
    return valor.strip().lower().replace("_", "-")


# =====================================================================
# 📡 DISPATCHER DE EVENTOS CLIENT-SIDE (SYSTEM_TOOLS)
# Maneja las herramientas cuyo resultado son eventos SSE para el frontend,
# sin necesidad de ejecutar código en el host.
# =====================================================================
async def _despachar_system_tool(tool_name: str, args: dict, user_id_norm: str) -> tuple[str | None, str]:
    """
    Evalúa si la tool invocada corresponde a una SYSTEM_TOOL (evento de cliente)
    y emite el SSE correspondiente.

    Devuelve: (sse_frame | None, resultado_texto)
    - sse_frame: el string SSE listo para yield, o None si no aplica.
    - resultado_texto: descripción humana del resultado para memoria episódica.
    """

    if tool_name == "open-media-app":
        platform = args.get("platform", "")
        platform_urls = {
            "spotify":       "https://open.spotify.com",
            "youtube-music": "https://music.youtube.com",
            "netflix":       "https://www.netflix.com",
        }
        url = platform_urls.get(platform, "https://google.com")
        payload = {"event": "OPEN-MEDIA", "media-platform": platform, "url": url, "status": "playing"}
        return (
            f"event: OPEN-MEDIA\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n",
            f"Ordenando al cliente que abra '{platform}' en pestaña."
        )

    if tool_name == "open-local-media":
        payload = {
            "event": "OPEN-LOCAL-MEDIA",
            "media-type": args.get("media-type", args.get("media_type", "")),
            "query": args.get("query", ""),
        }
        return (
            f"event: OPEN-LOCAL-MEDIA\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n",
            f"Reproduciendo media local: {payload}"
        )

    if tool_name == "open-system-app":
        payload = {
            "event": "CREATE-WINDOW",
            "window-id": f"app-{args.get('app-id', args.get('app_id', 'unknown'))}",
            "app-id": args.get("app-id", args.get("app_id", "")),
            "type": "system-app",
        }
        return (
            f"event: CREATE-WINDOW\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n",
            f"Abriendo aplicación de sistema: {payload['app-id']}"
        )

    if tool_name == "google-workspace-action":
        payload = {
            "event": "OPEN-IFRAME-APP",
            "app-service": args.get("service"),
            "app-action":  args.get("action"),
            "app-params":  args.get("params", {}),
        }
        return (
            f"event: OPEN-IFRAME-APP\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n",
            f"Abriendo interfaz de {args.get('service')} en el cliente."
        )

    if tool_name == "calculate-expression":
        exp = args.get("expression", "")
        try:
            val = eval(exp, {"__builtins__": None}, {})  # noqa: S307 — entorno sandboxeado
            return None, str(val)
        except Exception as e:
            return None, f"Error evaluando expresión: {e}"

    if tool_name == "set-wallpaper":
        payload = {"event": "SET-WALLPAPER", "image-url": args.get("imageUrl", args.get("image-url", ""))}
        return (
            f"event: SET-WALLPAPER\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n",
            "Fondo de pantalla actualizado."
        )

    if tool_name == "apply-css-theme":
        css_code = args.get("cssCode", args.get("css-code", ""))
        payload  = {"event": "SET-THEME", "css-code": css_code}
        try:
            themes_dir = os.path.join(BASE_DIR, "theme-profiles")
            os.makedirs(themes_dir, exist_ok=True)
            theme_path = os.path.join(themes_dir, f"{user_id_norm}.css")
            with open(theme_path, "w", encoding="utf-8") as f:
                f.write(css_code)
            logger.info(f"💾 [THEME] CSS físico persistido para '{user_id_norm}' en {theme_path}")
        except Exception as e:
            logger.error(f"❌ [THEME] Error guardando CSS: {e}")
        return (
            f"event: SET-THEME\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n",
            "Tema CSS inyectado y persistido globalmente."
        )

    if tool_name == "crear-acceso-directo":
        import time
        # Workaround: algunos LLMs locales envuelven todos los args bajo 'params'
        if "params" in args and isinstance(args.get("params"), dict):
            args = {**args, **args["params"]}
        payload = {
            "id": f"shortcut-{args.get('nombre', 'shortcut').lower().replace(' ', '-').replace('_', '-')}-{int(time.time())}",
            "nombre": args.get("nombre", ""),
            "icono": args.get("icono", "📌"),
            "tipo": args.get("tipo", "url"),
            "destino": args.get("destino", ""),
            "descripcion": args.get("descripcion", ""),
        }
        logger.info(f"📌 [SHORTCUT-DISPATCH] Enviando ADD-SHORTCUT al frontend: {payload}")
        return (
            f"event: ADD-SHORTCUT\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n",
            "Evento 'ADD-SHORTCUT' despachado al frontend exitosamente."
        )

    # La tool no es un evento de cliente: debe ejecutarse en el host
    return None, ""


# =====================================================================
# 🛡️ CONSTRUCCIÓN DEL SYSTEM PROMPT CONTEXTUALIZADO
# Se reconstruye por request para incluir memoria episódica del usuario.
# =====================================================================
def _construir_system_prompt(
    herramientas_str: str,
    bloque_memoria: str,
    terminal_id_norm: str,
    user_id_norm: str,
) -> str:
    return f"""Sos el kernel principal de AGNUX OS. Responde siempre de forma ejecutiva y concisa.
Tu identificador de sesión activo es terminal-id='{terminal_id_norm}', user-id='{user_id_norm}'.{bloque_memoria}

## HERRAMIENTAS DISPONIBLES
{herramientas_str}

**IMPORTANTE: SIEMPRE DEBES UTILIZAR LAS HERRAMIENTAS para acciones como cálculos matemáticos, inyección de CSS o control de multimedia. NUNCA asumas el cálculo mentalmente ni simules la acción en texto. INVOCA LA HERRAMIENTA CORRESPONDIENTE.**

## 1.0 REGLAS CONSTITUCIONALES DE NOMENCLATURA (ESTÁNDAR RFC-1035 / DNS / LINUX KERNEL)
- Está TAXATIVAMENTE PROHIBIDO el uso de guiones bajos ('_') en cualquier identificador de
  usuario, nombre de terminal, variable de contexto del host o nombre de herramienta dinámica.
- Todo identificador debe usar ÚNICAMENTE guiones medios ('-') o alfanumérico plano en minúsculas.
  Correcto: 'user-cristian', 'global-control-bomba', 'term-desktop-101'
  Incorrecto: 'user_cristian', 'global_control_bomba', 'term_desktop_101'
- Si autogenerás código en caliente, el archivo físico en disco y su registro deben usar
  guiones medios (ej. 'global-control-bomba.py').

## 2.0 GUÍA DE ESTILOS CSS (MOTOR DE TEMAS AGNUX)
La interfaz web está controlada por variables CSS en :root. Podés inyectar temas pisando:
- Colores base:    `--agnux-bg-color`, `--agnux-text-primary`, `--agnux-text-secondary`
- Acento:         `--agnux-accent`, `--agnux-accent-glow`, `--agnux-accent-dim`, `--agnux-accent-border`
- Glassmorphism:  `--agnux-panel-bg`, `--agnux-panel-solid`, `--agnux-panel-border`, `--agnux-panel-blur`
- Tipografía:     `--agnux-font-main`, `--agnux-font-clock`
Ejemplo hacker: `:root {{ --agnux-bg-color: #000; --agnux-accent: #00ff00; --agnux-font-main: 'Courier New'; }}`

## 3.0 NOTIFICACIONES PUSH (HYPERISLAND)
Si autogenerás una herramienta y necesitás notificar al usuario, usá WebSockets:
`from kernel_bus import notificar_frontend`
`await notificar_frontend(kwargs.get("terminal-id"), kwargs.get("user-id"), "Mensaje", "notif")`

## 4.0 REGLA DE AUTOGÉNESIS (CONSENTIMIENTO EXPLÍCITO)
Si el usuario pide algo para lo cual NO existe una herramienta, NO uses `autogenerar_nueva_tool`
directamente. Primero respondé explicándole que no tenés esa herramienta y preguntale si desea que
la programes. Sólo si el usuario responde afirmativamente, ejecutá `autogenerar_nueva_tool`.

## 5.0 SANDBOX DE EVALUACIÓN DE CÓDIGO (OBLIGATORIO)
Cuando el usuario pida generar, probar o mostrar código en el escritorio:
1. SIEMPRE llamá primero a `evaluar_codigo_sandbox` con el código completo y limpio (sin fences).
2. Si retorna 'ok=true': el código fue validado y el sistema lo envía automáticamente al escritorio.
3. Si retorna 'ok=false': leé el campo 'output' que contiene el traceback/error, corregí el código
   y volvé a llamar `evaluar_codigo_sandbox` con la versión corregida.
4. Máximo 3 intentos de corrección. Si falla 3 veces, informale al usuario el error final.
5. NUNCA envíes código al escritorio sin pasar por el sandbox primero.
"""


# =====================================================================
# ⚡ GENERADOR PRINCIPAL DE EVENTOS SSE — MOTOR AGNO NATIVO
# =====================================================================
async def procesar_generador_eventos(payload: TaskbarPrompt, is_google_connected: bool):
    """
    Generador asíncrono que orquesta el ciclo completo de inferencia de AGNUX:
      1. Protege el bus de inferencia con el semáforo FIFO OLLAMA-BUS-LOCK
      2. Recupera memoria episódica de Qdrant para el usuario
      3. Construye el system prompt contextualizado
      4. Usa agnux_agent.arun() con stream_events=True (motor Agno nativo)
      5. Mapea los RunResponseEvent a eventos SSE para Angular
      6. Despacha y ejecuta las tool calls interceptadas
      7. Persiste la memoria episódica del resultado en Qdrant
    """
    # ── Normalización constitucional de IDs ───────────────────────────
    terminal_id_norm = _normalizar_id(payload.terminal_id)
    user_id_norm     = _normalizar_id(payload.user_id)

    try:
        # ── 1. Guardia FIFO — proteger el bus de inferencia Ollama ────
        if OLLAMA_BUS_LOCK.locked():
            yield json.dumps({
                "event": "QUEUE-WAIT",
                "message": "Servidor ocupado. Solicitud en cola de espera en el Kernel..."
            }) + "\n"

        async with OLLAMA_BUS_LOCK:

            yield json.dumps({
                "event": "ROUTER-START",
                "message": "Inicializando Router Semántico en Memoria..."
            }) + "\n"

            # ── 2. Recarga de herramientas dinámicas en caliente ──────
            recargar_herramientas_dinamicas()

            # ── 3. Fusión del catálogo de herramientas disponibles ────
            tools_privadas       = CACHE_VECTORS["usuarios"].get(user_id_norm, {})
            system_tools_activas = {}
            for k, v in SYSTEM_TOOLS.items():
                if k == "googleWorkspaceAction" and not is_google_connected:
                    continue
                system_tools_activas[k] = {"schema": v["function"]}

            tools_disponibles = {
                **CACHE_VECTORS["sistema"],
                **tools_privadas,
                **system_tools_activas,
            }

            vector_usuario  = generar_vector_texto(payload.prompt)
            filtered_schemas = []

            for nombre_tool, data in tools_disponibles.items():
                score = 0.8  # TODO: similitud coseno real con vector_usuario
                yield json.dumps({"event": "ROUTER-SCORE", "tool": nombre_tool, "score": score}) + "\n"
                if score > 0.42:
                    filtered_schemas.append(data["schema"])

            herramientas_str = (
                json.dumps(filtered_schemas, indent=2, ensure_ascii=False)
                if filtered_schemas else "Ninguna herramienta adicional de sistema disponible."
            )

            # ── 4. Recuperación de memoria episódica (Omnisciencia) ───
            bloque_memoria = ""
            try:
                resultados = await qdrant_client.query_points(
                    collection_name=COLECCION_MEMORIA,
                    query=vector_usuario,
                    query_filter=Filter(
                        must=[FieldCondition(
                            key="user-id",
                            match=MatchValue(value=user_id_norm)
                        )]
                    ),
                    limit=3,
                )
                recuerdos = [
                    f"- {r.payload.get('contenido', '')}"
                    for r in resultados.points if r.score > 0.4
                ]
                if recuerdos:
                    bloque_memoria = (
                        "\n\n## RECUERDOS EPISÓDICOS RELEVANTES DEL USUARIO:\n"
                        + "\n".join(recuerdos)
                    )
            except Exception as e:
                logger.error(f"❌ [MEMORIA] Error recuperando contexto histórico: {e}")

            # ── 4.5. Recuperación de memoria a corto plazo (Historial Reciente) ──
            session_id = f"{terminal_id_norm}--{user_id_norm}"
            if session_id not in SESSION_HISTORY:
                SESSION_HISTORY[session_id] = []
            
            historial_reciente = "\n".join(SESSION_HISTORY[session_id][-6:])
            if historial_reciente:
                bloque_memoria += f"\n\n## HISTORIAL RECIENTE DE LA CONVERSACIÓN:\n{historial_reciente}"
            
            # Guardamos el prompt actual
            SESSION_HISTORY[session_id].append(f"Usuario: {payload.prompt}")

            # ── 5. Construcción del system prompt contextualizado ─────
            system_prompt = _construir_system_prompt(
                herramientas_str=herramientas_str,
                bloque_memoria=bloque_memoria,
                terminal_id_norm=terminal_id_norm,
                user_id_norm=user_id_norm,
            )

            # Inyectamos el system prompt de forma dinámica en el agente
            # sin mutar el objeto base permanentemente.
            agnux_agent.system_message = system_prompt

            # ── 6. STREAMING NATIVO CON AGNO ──────────────────────────
            # arun() con stream=True y stream_intermediate_steps=True emite:
            #   RunContentEvent       → tokens de texto
            #   ToolCallStartedEvent  → inicio de invocación de herramienta
            #   ToolCallCompletedEvent → resultado de la herramienta
            respuesta_completa  = ""
            ultima_tool_name    = None
            ultima_tool_args    = {}
            resultado_tool      = ""

            try:
                async for evento in agnux_agent.arun(
                    payload.prompt,
                    stream=True,
                    stream_intermediate_steps=True,
                    # Pasamos los identificadores de sesión como metadata
                    # para que las herramientas dinámicas puedan accederlos.
                    session_id=f"{terminal_id_norm}--{user_id_norm}",
                    additional_context={
                        "terminal-id": terminal_id_norm,
                        "user-id":     user_id_norm,
                    },
                ):
                    # En Agno 1.6+, arun(stream=True) devuelve objetos RunResponse.
                    # El tipo de evento puede estar en evento.event (RunEvent enum) 
                    # y los datos en evento.content o evento.tools.
                    event_type = str(getattr(evento, "event", getattr(evento, "type", "")))
                    
                    # ── INICIO de llamada a herramienta ───────────────
                    if "tool_call_started" in event_type.lower():
                        # Extraer info de la herramienta desde evento.tools (lista de diccionarios o objetos)
                        tools = getattr(evento, "tools", [])
                        if tools and len(tools) > 0:
                            tool_data = tools[0]
                            t_name = getattr(tool_data, "tool_name", getattr(tool_data, "name", "unknown_tool"))
                            t_args = getattr(tool_data, "tool_args", getattr(tool_data, "arguments", {}))
                            
                            ultima_tool_name = t_name.replace("_", "-")
                            ultima_tool_args = t_args

                            # Evento especial de UI para el sandbox
                            if ultima_tool_name == "evaluar-codigo-sandbox":
                                yield json.dumps({
                                    "event":    "SANDBOX-RUNNING",
                                    "message":  f"🐳 Evaluando código en contenedor Docker aislado...",
                                    "language": ultima_tool_args.get("lenguaje", "?") if isinstance(ultima_tool_args, dict) else "?",
                                }) + "\n"
                            else:
                                yield json.dumps({
                                    "event":    "TOOL-EXECUTE",
                                    "message":  f"Ejecutando herramienta: {ultima_tool_name}",
                                    "tool-name": ultima_tool_name,
                                }) + "\n"

                            logger.info(f"⚙️ [AGNO] ToolCallStarted: '{ultima_tool_name}' args={ultima_tool_args}")

                    # ── RESULTADO de llamada a herramienta ────────────
                    elif "tool_call_completed" in event_type.lower():
                        tools = getattr(evento, "tools", [])
                        if tools and len(tools) > 0:
                            tool_data = tools[0]
                            t_name = getattr(tool_data, "tool_name", getattr(tool_data, "name", "unknown_tool"))
                            t_result = getattr(tool_data, "content", getattr(tool_data, "result", ""))
                            
                            tool_name_result = t_name.replace("_", "-")
                            resultado_bruto  = str(t_result or "")
                            logger.info(f"✅ [AGNO] ToolCallCompleted: '{tool_name_result}' → {resultado_bruto[:120]}")

                            # ── 🐳 INTERCEPCIÓN DEL RESULTADO DE SANDBOX ────────
                            try:
                                sandbox_data = json.loads(resultado_bruto)
                                if sandbox_data.get("__sandbox_result"):
                                    lang        = sandbox_data.get("language", "")
                                    ok          = sandbox_data.get("ok", False)
                                    output      = sandbox_data.get("output", "")
                                    codigo      = sandbox_data.get("codigo", "")
                                    descripcion = sandbox_data.get("descripcion", "")
                                    exec_ms     = sandbox_data.get("execution-ms", 0)
                                    exit_code   = sandbox_data.get("exit-code", -1)

                                    if ok:
                                        logger.info(f"✅ [SANDBOX] Código aprobado en {exec_ms}ms. Enviando al escritorio.")
                                        sandbox_ok_payload = {
                                            "window-id":    "sandbox-output",
                                            "title":        f"🐳 Sandbox [{lang}] — {descripcion or 'Código Evaluado'}",
                                            "type":         "sandbox-result",
                                            "language":     lang,
                                            "codigo":       codigo,
                                            "output":       output,
                                            "execution-ms": exec_ms,
                                            "validated":    True,
                                        }
                                        yield f"event: SANDBOX-OK\ndata: {json.dumps(sandbox_ok_payload, ensure_ascii=False)}\n\n"
                                        resultado_tool = f"Código validado en sandbox ({exec_ms}ms). Enviado al escritorio."
                                    else:
                                        error_msg = sandbox_data.get("error-detail", "Error desconocido")
                                        logger.warning(f"⚠️ [SANDBOX] Código fallido (exit={exit_code}). Error: {output[:200]}")
                                        yield json.dumps({
                                            "event":      "SANDBOX-RETRY",
                                            "message":    f"🔄 El código falló. Corrigiendo automáticamente...",
                                            "exit-code":  exit_code,
                                            "error":      output[:500]
                                        }) + "\n"
                                        resultado_tool = f"SANDBOX FAIL: {error_msg}. Por favor corregí el código."

                                    yield json.dumps({"event": "TOOL-RESULT", "data": resultado_tool}) + "\n"
                                    continue
                            except (json.JSONDecodeError, TypeError, KeyError):
                                pass

                            # ── Interceptar si el resultado es un evento client-side ─
                            try:
                                resultado_json = json.loads(resultado_bruto)
                                if "__agnux_event" in resultado_json:
                                    evento_tipo    = resultado_json["__agnux_event"]
                                    sse_frame      = f"event: {evento_tipo}\ndata: {json.dumps(resultado_json, ensure_ascii=False)}\n\n"
                                    yield sse_frame
                                    resultado_tool = f"Evento '{evento_tipo}' despachado al frontend."
                                else:
                                    resultado_tool = resultado_bruto
                            except (json.JSONDecodeError, TypeError):
                                resultado_tool = resultado_bruto

                        # ── Dispatch de SYSTEM_TOOLS (wallpaper, CSS, media) ──
                        sse_frame_sys, resultado_sys = await _despachar_system_tool(
                            tool_name_result, ultima_tool_args, user_id_norm
                        )
                        if sse_frame_sys:
                            yield sse_frame_sys
                            resultado_tool = resultado_sys

                        yield json.dumps({
                            "event": "TOOL-RESULT",
                            "data":  resultado_tool
                        }) + "\n"

                    # ── 3. CHUNKS DE TEXTO (RESPUESTA DE IA) ──────────
                    else:
                        texto = getattr(evento, "content", "")
                        if texto and isinstance(texto, str):
                            respuesta_completa += texto
                            yield json.dumps({
                                "event":   "TEXT-CHUNK",
                                "content": texto,
                            }) + "\n"

            except Exception as e:
                logger.error(f"❌ [AGNO STREAM] Error en el stream del agente: {e}", exc_info=True)
                yield json.dumps({
                    "event": "ERROR",
                    "message": f"Error en el motor de inferencia Agno: {e}"
                }) + "\n"
                return

            # ── 7. Si el agente solo habló (sin tool call) → CREATE-WINDOW ──
            if respuesta_completa.strip():
                SESSION_HISTORY[session_id].append(f"AGNUX: {respuesta_completa.strip()}")
            
            if respuesta_completa.strip() and not ultima_tool_name:
                # ── Sniff: ¿el modelo escribió un JSON de herramienta como texto? ──
                texto_norm = respuesta_completa.strip()
                interceptado = False
                # Puede venir envuelto en ```json ... ``` o solo como JSON plano
                import re as _re
                json_match = _re.search(r'\{.*\}', texto_norm, _re.DOTALL)
                if json_match:
                    try:
                        candidato = json.loads(json_match.group(0))
                        css_code = candidato.get("cssCode") or candidato.get("css-code")
                        image_url = candidato.get("imageUrl") or candidato.get("image-url")
                        agnux_event = candidato.get("__agnux_event")

                        if css_code:
                            logger.info("🎨 [INTERCEPT] Respuesta de texto contiene cssCode — despachando SET-THEME")
                            payload_tema = {"event": "SET-THEME", "css-code": css_code}
                            yield f"event: SET-THEME\ndata: {json.dumps(payload_tema, ensure_ascii=False)}\n\n"
                            try:
                                themes_dir = os.path.join(BASE_DIR, "theme-profiles")
                                os.makedirs(themes_dir, exist_ok=True)
                                with open(os.path.join(themes_dir, f"{user_id_norm}.css"), "w", encoding="utf-8") as f:
                                    f.write(css_code)
                            except Exception:
                                pass
                            interceptado = True

                        elif image_url:
                            logger.info("🖼️ [INTERCEPT] Respuesta de texto contiene imageUrl — despachando SET-WALLPAPER")
                            yield f"event: SET-WALLPAPER\ndata: {json.dumps({'event': 'SET-WALLPAPER', 'image-url': image_url}, ensure_ascii=False)}\n\n"
                            interceptado = True

                        elif agnux_event:
                            logger.info(f"⚡ [INTERCEPT] Respuesta de texto contiene __agnux_event='{agnux_event}' — re-despachando")
                            yield f"event: {agnux_event}\ndata: {json.dumps(candidato, ensure_ascii=False)}\n\n"
                            interceptado = True

                    except (json.JSONDecodeError, TypeError):
                        pass

                if not interceptado:
                    payload_ventana = {
                        "window-id": "agnux-ai-window",
                        "title":     "🧠 AGNUX OS Core — IA",
                        "content":   texto_norm,
                        "type":      "terminal",
                    }
                    yield f"event: CREATE-WINDOW\ndata: {json.dumps(payload_ventana, ensure_ascii=False)}\n\n"

            logger.info("🔌 [KERNEL] Tarea cumplida. Liberando canal de intent.")

            # ── 8. Persistencia de memoria episódica (fire-and-forget) ──
            texto_memoria = f"Usuario dijo: {payload.prompt}\nAGNUX respondió: {respuesta_completa}"
            if ultima_tool_name:
                texto_memoria += f"\nAGNUX ejecutó la herramienta '{ultima_tool_name}' → {resultado_tool}"

            asyncio.create_task(guardar_recuerdo_qdrant(
                user_id=user_id_norm,
                tipo_evento="chat-interaccion",
                contenido=texto_memoria,
            ))

            # ── 9. Escalada de privilegios: promover tool global a RAM Kernel ──
            if ultima_tool_name == "autogenerar-nueva-tool":
                nombre_func = ultima_tool_args.get("nombre_funcion", "")
                nombre_norm = nombre_func.replace("_", "-").lower()
                if nombre_norm.startswith("global-"):
                    CACHE_VECTORS["sistema"][nombre_norm] = {
                        "vector": generar_vector_texto(ultima_tool_args.get("descripcion_docstring", "")),
                        "schema": {
                            "name":        nombre_norm,
                            "description": ultima_tool_args.get("descripcion_docstring", ""),
                            "parameters":  {"type": "object", "properties": {}},
                        }
                    }
                    logger.info(
                        f"🌐 [RAM KERNEL] Herramienta '{nombre_norm}' promovida a GLOBAL en la RAM del Kernel."
                    )

    finally:
        logger.info("🔌 [KERNEL] Limpiando recursos del generador asíncrono de intenciones.")
