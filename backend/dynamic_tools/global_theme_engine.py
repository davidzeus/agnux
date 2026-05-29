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

    Debes devolver ÚNICAMENTE un objeto JSON estricto con la clave "css". El valor debe ser código CSS en crudo.
    
    ES VITAL QUE SIEMPRE INCLUYAS LA REESCRITURA DE LAS VARIABLES GLOBALES EN `:root` PARA QUE LAS VENTANAS Y PANELES CAMBIEN DE COLOR.
    Las variables son:
    --agnux-accent
    --agnux-accent-glow
    --agnux-accent-dim
    --agnux-accent-hover
    --agnux-accent-border
    --agnux-panel-bg (Fondo de las ventanas flotantes, ej rgba(0,0,0,0.8))
    --agnux-panel-solid (Fondo sólido)
    --agnux-panel-border (Bordes de ventanas)
    --agnux-font-main
    --agnux-font-clock
    --agnux-text-primary
    --agnux-text-secondary

    Aquí tienes un mapeo en vivo de la arquitectura actual del DOM de la interfaz:
    ```
    {dom_context}
    ```

    Después del `:root`, puedes aplicar tu "Modo Anarquía Visual" inyectando estilos crudos a los selectores exactos que acabas de ver en el DOM escaneado.
    
    Retorna SOLO el objeto JSON. Ejemplo:
    {{
        "css": ":root {{ --agnux-panel-bg: rgba(20,20,20,0.9); --agnux-accent: #ff0000; }} .window-header {{ font-weight: bold; }}"
    }}
    """

    payload = {
        "model": "qwen2.5-coder:1.5b",
        "prompt": prompt_ia,
        "stream": False,
        "format": "json"
    }

    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url_generate, json=payload, timeout=20.0)
            if res.status_code != 200:
                return f"ERROR KERNEL: Falla en inferencia de diseño (HTTP {res.status_code})"
            
            respuesta_json = res.json().get("response", "").strip()
            import logging
            logger = logging.getLogger("AGNUX-KERNEL-BUS")
            logger.info(f"🎨 [QWEN THEME ENGINE] Respuesta cruda: {respuesta_json}")
            
            try:
                css_vars = json.loads(respuesta_json)
            except json.JSONDecodeError:
                # Intento de parseo de rescate
                import re
                match = re.search(r'\{.*\}', respuesta_json, re.DOTALL)
                if match:
                    css_vars = json.loads(match.group(0))
                else:
                    return f"ERROR KERNEL: El modelo no devolvió JSON válido. Recibido: {respuesta_json}"

            # Construir payload para el Frontend con CSS crudo
            ws_payload = {
                "type": "theme_update",
                "data": {"css": css_vars.get("css", "") if isinstance(css_vars, dict) else css_vars}
            }
            
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
