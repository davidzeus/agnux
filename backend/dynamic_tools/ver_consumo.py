"""
Definición autogenerada por AGNUX OS Core.
"""

def ver_consumo():
    """Calcula y muestra el consumo acumulado de tokens de Gemini y el costo estimado."""
    import os
    import json

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_path = os.path.join(base_dir, "dynamic_tools", "historial_consumo.json")

    if not os.path.exists(log_path):
        return "Aún no hay registros de consumo en el sistema operativo."

    try:
        with open(log_path, "r") as f:
            registros = json.load(f)

        total_input = sum(r.get("prompt_tokens", 0) for r in registros)
        total_output = sum(r.get("candidates_tokens", 0) for r in registros)
        total_peticiones = len(registros)

        # Precios de referencia de Gemini 2.5 Flash:
        # Input: $0.075 por millón de tokens | Output: $0.30 por millón de tokens
        costo_input = (total_input / 1_000_000) * 0.075
        costo_output = (total_output / 1_000_000) * 0.30
        costo_total = costo_input + costo_output

        reporte = (
            f"📊 REPORTE DE CONSUMO DE GEMINI CLOUD:\n"
            f"• Peticiones Totales: {total_peticiones}\n"
            f"• Tokens de Entrada (Prompt): {total_input}\n"
            f"• Tokens de Salida (Respuesta): {total_output}\n"
            f"• Acumulado Total: {total_input + total_output} tokens\n"
            f"• Costo Estimado Total: ${costo_total:.6f} USD"
        )
        return reporte

    except Exception as e:
        return f"Error al procesar el reporte de consumo: {str(e)}"