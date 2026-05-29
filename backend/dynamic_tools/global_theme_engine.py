import os
import json
import httpx
from kernel_bus import manager

async def global_theme_engine(style_prompt: str, **kwargs) -> str:
    """
    Motor de Inteligencia Artificial para cambiar el tema/diseño de la interfaz visual del sistema.
    Recibe un prompt de estilo (ej. 'estilo macOS oscuro', 'colores cálidos', 'modo hacker')
    y genera las variables CSS correspondientes para inyectarlas en vivo en la pantalla del usuario.
    """
    terminal_id = kwargs.get("__terminal_id")
    user_id = kwargs.get("__user_id")
    
    if not terminal_id or not user_id:
        return "ERROR: Contexto de terminal_id o user_id ausente. No se puede inyectar el estilo."

    ollama_base = os.getenv("OLLAMA_HOST", "http://10.10.0.48:11434").rstrip("/")
    url_generate = f"{ollama_base}/api/generate"

    # Escaneo en vivo de la interfaz actual (DOM real)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    frontend_components_dir = os.path.join(base_dir, "frontend", "src", "app", "components")
    dom_context = ""
    try:
        import glob
        html_files = glob.glob(os.path.join(frontend_components_dir, "**", "*.html"), recursive=True)
        for html_file in html_files:
            component_name = os.path.basename(os.path.dirname(html_file))
            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()
                # Limpiar bindings de Angular para no confundir a la IA
                import re
                content = re.sub(r'\[.*?\]=".*?"', '', content)
                content = re.sub(r'\(.*?\)=".*?"', '', content)
                content = re.sub(r'\*ngIf=".*?"', '', content)
                content = re.sub(r'\*ngFor=".*?"', '', content)
                content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
                # Extraer solo las etiquetas, ids y clases
                tags = re.findall(r'<[a-zA-Z0-9\-]+(?:[^>]*class="([^"]+)")?(?:[^>]*id="([^"]+)")?[^>]*>', content)
                
                dom_context += f"Componente: {component_name}\n"
                for tag in tags[:20]: # Limitar para no explotar el contexto
                    classes = f" class='{tag[0]}'" if tag[0] else ""
                    ids = f" id='{tag[1]}'" if tag[1] else ""
                    if classes or ids:
                        dom_context += f"- Elemento {classes}{ids}\n"
    except Exception as e:
        dom_context = f"(Error escaneando DOM: {e})"

    prompt_ia = f"""
    Eres un diseñador experto en UI/UX CSS y un hacker visual. El usuario solicitó el siguiente estilo visual para su sistema operativo web:
    "{style_prompt}"

    ES OBLIGATORIO que tu respuesta comience redefiniendo el bloque `:root` con las siguientes variables globales, asignándoles colores y valores reales (NO uses referencias a otras variables, usa HEX o RGBA reales que encajen con el estilo pedido):
    :root {{
        --agnux-accent: ...;
        --agnux-accent-glow: ...;
        --agnux-accent-dim: ...;
        --agnux-accent-hover: ...;
        --agnux-accent-border: ...;
        --agnux-panel-bg: ...;
        --agnux-panel-solid: ...;
        --agnux-panel-border: ...;
        --agnux-font-main: ...;
        --agnux-font-clock: ...;
        --agnux-text-primary: ...;
        --agnux-text-secondary: ...;
    }}

    Aquí tienes un mapeo en vivo de la arquitectura actual del DOM de la interfaz:
    ```
    {dom_context}
    ```

    Tu tarea es escribir un bloque de código CSS puro que reestructure y rediseñe completamente la interfaz para lograr el estilo: "{style_prompt}".
    
    INSTRUCCIONES CLAVES:
    1. DEBES escribir el bloque `:root` con los nuevos valores, tal como se indicó arriba.
    2. Luego del `:root`, eres LIBRE de modificar la geometría: usa `padding`, `margin`, `border-radius`, `box-shadow`, `backdrop-filter` directamente sobre las clases del DOM (ej. `.window`, `.window-header`, `.cyber-input`, `.hyper-island`).
    3. Asegúrate de NO referenciar variables inexistentes. Usa valores reales o las variables que tú mismo redefiniste en el `:root`.
    4. NO expliques nada. Devuelve ÚNICAMENTE el código envuelto en ```css ... ```.
    """

    payload = {
        "model": "deepseek-coder:6.7b",
        "prompt": prompt_ia,
        "stream": False,
        "keep_alive": 0
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url_generate, json=payload, timeout=20.0)
            if res.status_code != 200:
                return f"ERROR KERNEL: Falla en inferencia de diseño (HTTP {res.status_code})"
            
            respuesta_bruta = res.json().get("response", "").strip()
            import logging
            logger = logging.getLogger("AGNUX-KERNEL-BUS")
            logger.info(f"🎨 [DEEPSEEK THEME ENGINE] Respuesta cruda: {respuesta_bruta}")
            
            import re
            # Intentar extraer el bloque CSS
            match = re.search(r'```css\s*(.*)', respuesta_bruta, re.DOTALL | re.IGNORECASE)
            if match:
                css_crudo = match.group(1)
                # Quitar posibles backticks de cierre
                css_crudo = re.sub(r'```\s*$', '', css_crudo).strip()
            else:
                # Si el modelo no usó los backticks, asumimos que todo es CSS
                css_crudo = respuesta_bruta.replace('```', '').strip()

            # Construir payload para el Frontend con CSS crudo
            ws_payload = {
                "type": "theme_update",
                "data": {"css": css_crudo}
            }
            
            # --- PERSISTENCIA FÍSICA ---
            theme_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "theme_profiles")
            os.makedirs(theme_dir, exist_ok=True)
            theme_path = os.path.join(theme_dir, f"{user_id}.css")
            with open(theme_path, "w", encoding="utf-8") as f:
                f.write(css_crudo)
            logger.info(f"💾 [THEME ENGINE] CSS físico guardado en: {theme_path}")
            # ---------------------------
            
            # Notificar al bus
            await manager.send_personal_message(terminal_id, user_id, ws_payload)
            
            # Alertar visualmente en HyperIsland que el tema cambió
            notif_payload = {
                "type": "notification",
                "data": {
                    "message": f"Estilo '{style_prompt}' aplicado en vivo.",
                    "category": "system"
                }
            }
            await manager.send_personal_message(terminal_id, user_id, notif_payload)

            return f"Estilo dinámico aplicado: {style_prompt}"

    except Exception as e:
        return f"ERROR KERNEL: Falla física en el generador de temas: {e}"
