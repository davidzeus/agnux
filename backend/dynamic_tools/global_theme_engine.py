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
    Eres un diseñador experto en UI/UX CSS y un hacker visual. El usuario solicitó el siguiente estilo visual para su sistema operativo web:
    "{style_prompt}"

    Debes devolver ÚNICAMENTE un objeto JSON estricto con la clave "css". El valor de esa clave debe ser el código CSS en crudo que reemplace por completo las variables CSS definidas en la raíz del documento o directamente sobreescriba selectores existentes como `.desktop-env`, `.hyper-island`, `.cyber-input`, `.clock-time`.
    
    Puedes hacer uso del modo Anarquía Visual, inyectando estilos agresivos, animaciones keyframes, filtros o reemplazando todo el `:root`.
    
    Usa colores hexagonales o rgba válidos. Usa fuentes genéricas o de Google Fonts populares.

    Retorna SOLO el objeto JSON, nada más. Ejemplo:
    {{
        "css": ":root {{ --agnux-bg-color: #fff; --agnux-accent: #000; }}"
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
