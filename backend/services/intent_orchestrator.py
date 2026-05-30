import os
import json
import re
import asyncio
import httpx

from qdrant_client.models import Filter, FieldCondition, MatchValue

from core.config import logger, OLLAMA_HOST, AGNUX_ACTIVE_MODEL
from core.memory import (
    OLLAMA_BUS_LOCK, CACHE_VECTORS, qdrant_client, COLECCION_MEMORIA,
    generar_vector_texto, guardar_recuerdo_qdrant
)
from schemas.models import TaskbarPrompt
from services.tools_service import SYSTEM_TOOLS, ejecutar_herramienta_local

async def procesar_generador_eventos(payload: TaskbarPrompt, is_google_connected: bool):
    try:
        # Verificación del semáforo FIFO
        if OLLAMA_BUS_LOCK.locked():
            yield json.dumps({"event": "QUEUE_WAIT", "message": "Servidor ocupado. Solicitud en cola de espera en el Kernel..."}) + "\n"

        # Adquiriendo candado de concurrencia
        async with OLLAMA_BUS_LOCK:
            base_host = OLLAMA_HOST.rstrip("/")
            url_ollama_universal = f"{base_host}/api/generate"
            modelo_activo = AGNUX_ACTIVE_MODEL

            yield json.dumps({"event": "ROUTER_START", "message": "Inicializando Router Semántico en Memoria..."}) + "\n"

            # Fusión virtual jerárquica con normalización de ID
            id_normalizado = payload.user_id.replace("_", "-")
            tools_privadas = CACHE_VECTORS["usuarios"].get(id_normalizado, {})
            
            system_tools_converted = {}
            for k, v in SYSTEM_TOOLS.items():
                if k == "googleWorkspaceAction" and not is_google_connected:
                    continue
                system_tools_converted[k] = {"schema": v["function"]}

            tools_disponibles = {**CACHE_VECTORS["sistema"], **tools_privadas, **system_tools_converted}

            vector_usuario = generar_vector_texto(payload.prompt)
            filtered_tools = []

            # Router Semántico y emisión geométrica en tiempo real
            for nombre_tool, data in tools_disponibles.items():
                score = 0.8 # TODO futuro: utilizar similitud de cosenos real aquí
                yield json.dumps({"event": "ROUTER_SCORE", "tool": nombre_tool, "score": score}) + "\n"

                # Umbral de corte calibrado para ministral:latest
                if score > 0.42:
                    filtered_tools.append(data["schema"])

            # 💡 HACK: La autogénesis SIEMPRE debe estar disponible como última línea de defensa
            filtered_tools.append({
                "name": "autogenerar_nueva_tool",
                "description": "Se activa para programar una nueva herramienta (código python) cuando ninguna de las herramientas actuales puede satisfacer la petición del usuario. Utiliza esto para crear nuevas integraciones o comportamientos.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "nombre_funcion": {"type": "string"},
                        "codigo_python": {"type": "string", "description": "El código fuente en Python de la herramienta."},
                        "descripcion_docstring": {"type": "string"}
                    },
                    "required": ["nombre_funcion", "codigo_python", "descripcion_docstring"]
                }
            })

            # RECUPERACIÓN DE MEMORIA EPISÓDICA (OMNISCIENCIA)
            try:
                resultados_memoria = await qdrant_client.search(
                    collection_name=COLECCION_MEMORIA,
                    query_vector=vector_usuario,
                    query_filter=Filter(
                        must=[
                            FieldCondition(
                                key="user_id",
                                match=MatchValue(value=payload.user_id),
                            )
                        ]
                    ),
                    limit=3
                )
                recuerdos_str = "\n".join([f"- {r.payload.get('contenido', '')}" for r in resultados_memoria if r.score > 0.4])
                bloque_memoria = f"\n\n## RECUERDOS EPISÓDICOS RELEVANTES DEL USUARIO:\n{recuerdos_str}" if recuerdos_str else ""
            except Exception as e:
                logger.error(f"❌ [MEMORIA] Error al recuperar contexto histórico: {e}")
                bloque_memoria = ""

            herramientas_disponibles_str = json.dumps(filtered_tools, indent=2, ensure_ascii=False) if filtered_tools else "Ninguna"

            SYSTEM_PROMPT = f"""Sos el kernel principal de AGNUX OS. Responde siempre corto y ejecutivo.{bloque_memoria}

## HERRAMIENTAS DISPONIBLES:
{herramientas_disponibles_str}

Para ejecutar una herramienta existente, DEBES responder ÚNICAMENTE con un bloque JSON como este (y nada más):
```json
{{
    "tool_call": "nombre_de_la_herramienta",
    "arguments": {{"param1": "valor"}}
}}
```

## 2.1 REGLAS ESTRICTAS DE NOMENCLATURA DE RED (ESTÁNDAR DE KERNEL LINUX Y DNS)
- Está TAXATIVAMENTE PROHIBIDO el uso de guiones bajos ('_') en cualquier identificador de usuario, nombre de terminal, o nombre de herramienta dinámica que interactúe con el host. El guión bajo rompe la sintaxis de interfaces de WireGuard y las especificaciones de Hostnames de internet (RFC 1035).
- Todo identificador debe normalizarse utilizando única y exclusivamente guiones medios ('-') o formato alfanumérico plano en minúsculas (ejemplo correcto: 'user-cristian', 'global-calculadora', 'term-desktop-101').
- Si vas a autogenerar código en caliente para una nueva herramienta, el archivo físico en disco y su registro semántico deben usar guiones medios (ej. 'global-control-bomba.py').

## REGLA DE AUTOGÉNESIS (CONSENTIMIENTO EXPLÍCITO)
Si el usuario te pide una tarea para la cual NO existe una herramienta, **NO uses `autogenerar_nueva_tool` directamente**. Primero debes responderle (sin usar formato JSON de herramienta) explicándole que no tienes la herramienta y preguntándole si desea que la programes. Sólo si el usuario responde afirmativamente, entonces en tu siguiente respuesta ejecutarás `autogenerar_nueva_tool`.

## NOTIFICACIONES PUSH (HYPERISLAND)
Si estás autogenerando una herramienta y necesitas notificar al usuario, puedes usar WebSockets puros.
Importa de forma asíncrona: `from kernel_bus import notificar_frontend` y ejecuta:
`await notificar_frontend(kwargs.get("__terminal_id"), kwargs.get("__user_id"), "Mensaje", "notif")`
"""

            payload_ollama = {
                "model": modelo_activo,
                "prompt": f"{SYSTEM_PROMPT}\n\nUser: {payload.prompt}",
                "stream": True
            }

            tool_call_detected = None
            argumentos_acumulados = ""

            try:
                # Streaming multiplexado al bus Ollama
                async with httpx.AsyncClient() as client:
                    async with client.stream("POST", url_ollama_universal, json=payload_ollama, timeout=60.0) as response:
                        if response.status_code != 200:
                            yield json.dumps({"event": "ERROR", "message": f"Bus Inferencia Caído. HTTP {response.status_code}"}) + "\n"
                            return

                        # 1. Consolidamos el texto que nos mandó Ministral
                        respuesta_completa = ""
                        async for line in response.aiter_lines():
                            if line:
                                try:
                                    data = json.loads(line)
                                    token = data.get("response", "")
                                    if token:
                                        respuesta_completa += token
                                        texto_limpio = respuesta_completa.strip()
                                        
                                        if not texto_limpio:
                                            continue
                                            
                                        is_tool_call_stream = texto_limpio.startswith("{") or texto_limpio.startswith("```")
                                        
                                        if not is_tool_call_stream:
                                            if len(texto_limpio) == len(token.strip()) and len(respuesta_completa) > len(token):
                                                yield f"event: TOKEN\ndata: {json.dumps(respuesta_completa)}\n\n"
                                            else:
                                                yield f"event: TOKEN\ndata: {json.dumps(token)}\n\n"
                                except Exception:
                                    continue

                        # 2. 🧠 EL CIRCUITO QUE SE HABÍA ROTO: Evaluación de acción
                        logger.info(f"🧠 [KERNEL AGENTE] Evaluando acción para la respuesta: {respuesta_completa}")
                        
                        bloque_json = re.search(r'```json\s*(.*?)\s*```', respuesta_completa, re.DOTALL)
                        bloque_python = re.search(r'```python\s*(.*?)\s*```', respuesta_completa, re.DOTALL)
                        match_nombre = re.search(r'`([^`]+)\.py`', respuesta_completa) or re.search(r'\*\*Nombre sugerido:\*\*\s*`([^`]+)`', respuesta_completa)

                        json_str = None
                        if bloque_json:
                            json_str = bloque_json.group(1)
                        else:
                            try:
                                json.loads(respuesta_completa)
                                json_str = respuesta_completa
                            except Exception:
                                match_raw = re.search(r'\{.*"tool_call".*\}', respuesta_completa, re.DOTALL)
                                if match_raw:
                                    json_str = match_raw.group(0)

                        if json_str:
                            try:
                                json_data = json.loads(json_str)
                                if "tool_call" in json_data:
                                    tool_call_detected = json_data["tool_call"]
                                    argumentos_acumulados = json.dumps(json_data.get("arguments", {}))
                                    logger.info(f"⚙️ [KERNEL AGENTE] Llamada a tool existente detectada: {tool_call_detected}")
                            except Exception as e:
                                logger.error(f"❌ Error parseando tool_call JSON: {e}")
                        
                        if not tool_call_detected and bloque_python and match_nombre:
                            tool_call_detected = "autogenerar_nueva_tool"
                            nombre_func = match_nombre.group(1).replace(".py", "")
                            argumentos_acumulados = json.dumps({
                                "nombre_funcion": nombre_func,
                                "codigo_python": bloque_python.group(1),
                                "descripcion_docstring": "Tool generada en tiempo de ejecución"
                            })
                            logger.info(f"⚙️ [KERNEL AGENTE] Tool heurística detectada en stream: {nombre_func}")
                        
                        if not tool_call_detected:
                            # Si la IA determinó que es una respuesta directa o texto para el operador,
                            payload_ventana = {
                                "window_id": "agnux-ai-window",
                                "title": "🧠 AGNUX OS Core - Ministral IA",
                                "content": respuesta_completa,
                                "type": "terminal"
                            }
    
                            yield f"event: CREATE_WINDOW\ndata: {json.dumps(payload_ventana, ensure_ascii=False)}\n\n"
    
                            logger.info("🔌 [KERNEL AGENTE] Tarea cumplida. Liberando canal de intent de forma inmediata.")
                            
                            # Guardar memoria del chat
                            asyncio.create_task(guardar_recuerdo_qdrant(
                                user_id=payload.user_id,
                                tipo_evento="chat_interaccion",
                                contenido=f"Usuario dijo: {payload.prompt}\nAGNUX respondió: {respuesta_completa}"
                            ))
                            
                            return

            except Exception as e:
                yield json.dumps({"event": "ERROR", "message": f"Ollama Stream Network Error: {e}"}) + "\n"
                return

            if tool_call_detected:
                yield json.dumps({"event": "TOOL_EXECUTE", "message": f"Ejecución solicitada a Kernel: {tool_call_detected}"}) + "\n"
                try:
                    args = json.loads(argumentos_acumulados) if argumentos_acumulados else {}
                    
                    # =================================================================
                    # DISPATCHER DE SYSTEM_TOOLS (Intercepción Directa)
                    # =================================================================
                    if tool_call_detected == "openMediaApp":
                        platform = args.get("platform")
                        platform_urls = {
                            "spotify": "https://open.spotify.com",
                            "youtubeMusic": "https://music.youtube.com",
                            "netflix": "https://www.netflix.com"
                        }
                        url = platform_urls.get(platform, "https://google.com")
                        media_payload = {
                            "event": "OPEN_MEDIA",
                            "mediaPlatform": platform,
                            "url": url,
                            "status": "playing"
                        }
                        yield f"event: OPEN_MEDIA\ndata: {json.dumps(media_payload)}\n\n"
                        resultado_fierros = f"Ordenando al cliente web que abra {platform} en una nueva pestaña."
                        
                    elif tool_call_detected == "googleWorkspaceAction":
                        iframe_payload = {
                            "event": "OPEN_IFRAME_APP",
                            "appService": args.get("service"),
                            "appAction": args.get("action"),
                            "appParams": args.get("params", {})
                        }
                        yield f"event: OPEN_IFRAME_APP\ndata: {json.dumps(iframe_payload)}\n\n"
                        resultado_fierros = f"Abriendo interfaz de {args.get('service')} en el cliente."
                        
                    elif tool_call_detected == "calculateExpression":
                        exp = args.get("expression", "")
                        try:
                            val = eval(exp, {"__builtins__": None}, {})
                            resultado_fierros = str(val)
                        except Exception as e:
                            resultado_fierros = f"Error evaluando expresión: {e}"
                            
                    elif tool_call_detected == "setWallpaper":
                        wallpaper_payload = {
                            "event": "SET_WALLPAPER",
                            "imageUrl": args.get("imageUrl")
                        }
                        yield f"event: SET_WALLPAPER\ndata: {json.dumps(wallpaper_payload)}\n\n"
                        resultado_fierros = "Fondo de pantalla actualizado con éxito."
                        
                    elif tool_call_detected == "applyCssTheme":
                        css_code = args.get("cssCode", "")
                        theme_payload = {
                            "event": "SET_THEME",
                            "cssCode": css_code
                        }
                        try:
                            from core.config import BASE_DIR
                            import os
                            themes_dir = os.path.join(BASE_DIR, "theme_profiles")
                            os.makedirs(themes_dir, exist_ok=True)
                            theme_path = os.path.join(themes_dir, f"{payload.user_id}.css")
                            with open(theme_path, "w", encoding="utf-8") as f:
                                f.write(css_code)
                            logger.info(f"💾 [THEME] Tema CSS físico guardado para {payload.user_id}")
                        except Exception as e:
                            logger.error(f"❌ [THEME] Error guardando CSS: {e}")
                            
                        yield f"event: SET_THEME\ndata: {json.dumps(theme_payload)}\n\n"
                        resultado_fierros = "Estilo CSS inyectado y persistido globalmente."
                        
                    else:
                        resultado_fierros = await ejecutar_herramienta_local(
                            tool_call_detected, 
                            args, 
                            terminal_id=payload.terminal_id, 
                            user_id=payload.user_id
                        )

                    yield json.dumps({"event": "TOOL_RESULT", "data": resultado_fierros}) + "\n"

                    # Guardar memoria de la tool
                    asyncio.create_task(guardar_recuerdo_qdrant(
                        user_id=payload.user_id,
                        tipo_evento="ejecucion_herramienta",
                        contenido=f"Usuario pidió: {payload.prompt}\nAGNUX ejecutó la herramienta '{tool_call_detected}' con los argumentos: {args}\nResultado: {resultado_fierros}"
                    ))

                    # Criterio de promoción: ¿es una tool de sistema u over-ride global?
                    if tool_call_detected == "autogenerar_nueva_tool" and args.get("nombre_funcion", "").startswith("global_"):
                        nombre_func = args["nombre_funcion"]
                        CACHE_VECTORS["sistema"][nombre_func] = {
                            "vector": generar_vector_texto(args.get("descripcion_docstring", "")),
                            "schema": {
                                "name": nombre_func,
                                "description": args.get("descripcion_docstring", ""),
                                "parameters": {"type": "object", "properties": {}}
                            }
                        }
                        logger.info(f"🌐 [RAM KERNEL] Escalada de privilegios: Herramienta '{nombre_func}' promovida a GLOBAL.")

                except Exception as e:
                    yield json.dumps({"event": "ERROR", "message": f"Falla física en tool_call: {e}"}) + "\n"
    finally:
        logger.info("🔌 [KERNEL AGENTE] Limpiando recursos del generador asíncrono.")
