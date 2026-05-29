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

    prompt_ia = f"""
    Eres un diseñador experto en UI/UX CSS. El usuario solicitó el siguiente estilo visual para su sistema operativo web:
    "{style_prompt}"

    Debes devolver ÚNICAMENTE un objeto JSON estricto con las siguientes variables CSS globales ajustadas a este estilo.
    Usa colores hexagonales o rgba válidos. Usa fuentes genéricas o de Google Fonts populares (ej. 'Inter', 'Roboto', 'monospace', 'sans-serif').
    
    Las variables son:
    "--agnux-bg-color": Color de fondo sólido oscuro o claro según el tema.
    "--agnux-bg-image": (Opcional) Puedes poner 'none' o dejarlo como 'url(...)'. Mejor pon 'none' para priorizar colores lisos si el estilo es minimalista.
    "--agnux-accent": Color principal de acento.
    "--agnux-accent-glow": Color de sombra (box-shadow) del acento.
    "--agnux-accent-dim": Color de acento con mucha transparencia.
    "--agnux-accent-hover": Color de acento para hover.
    "--agnux-accent-border": Color para bordes de paneles con acento.
    "--agnux-panel-bg": Color de fondo de los paneles translúcidos (ej. rgba(0,0,0,0.5) para dark, rgba(255,255,255,0.7) para light).
    "--agnux-panel-solid": Fondo sólido para la HyperIsland.
    "--agnux-panel-border": Borde sutil general.
    "--agnux-panel-blur": Nivel de blur, ej. 'blur(20px)'.
    "--agnux-font-main": Fuente principal.
    "--agnux-font-clock": Fuente para el reloj grande.
    "--agnux-text-primary": Color de texto primario (blanco o negro).
    "--agnux-text-secondary": Color de texto secundario (grisáceo).

    Retorna SOLO el objeto JSON, nada más.
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

            # Construir payload para el Frontend
            ws_payload = {
                "type": "theme_update",
                "data": css_vars
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
