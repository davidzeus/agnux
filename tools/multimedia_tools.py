# tools/multimedia_tools.py
import subprocess
import os

def ejecutar_musica_fondo(busqueda_o_url: str) -> str:
    """
    Busca en YouTube y reproduce audio en segundo plano usando MPV de forma desacoplada.
    Permite al usuario seguir interactuando con el sistema operativo mientras suena música.
    :param busqueda_o_url: El término a buscar (ej: 'lofi hip hop') o un enlace directo.
    """
    try:
        # --no-video le dice a MPV que solo procese el stream de audio (ahorra CPU y RAM)
        # --ytdl-format="bestaudio" asegura que baje el flujo más liviano y rápido
        # Usamos subprocess.Popen con shell=True para desvincular el proceso por completo del backend
        comando = f"mpv --no-video --ytdl-format=bestaudio 'ytdl://ytsearch:{busqueda_o_url}' > /dev/null 2>&1 &"
        subprocess.Popen(comando, shell=True)
        
        return f"SUCCESS_AUDIO: Sintonizando de fondo '{busqueda_o_url}'. Los parlantes de Lubuntu están activos."
    except Exception as e:
        return f"Error al intentar inicializar el subsistema multimedia: {str(e)}"

def controlar_reproductor_global(accion: str) -> str:
    """
    Controla de forma nativa la reproduccion de los procesos MPV en fondo.
    :param accion: Valores aceptados: 'pausa', 'reproducir', 'detener'.
    """
    accion_clean = accion.lower().strip()
    
    try:
        if accion_clean == "detener":
            # Mata todos los procesos de MPV corriendo en el host
            os.system("killall mpv")
            return "SUCCESS_AUDIO_STOP: Reproducción de fondo completamente detenida."
            
        elif accion_clean == "pausa":
            # Envía la señal SIGSTOP para congelar el proceso sin cerrarlo
            os.system("killall -SIGSTOP mpv")
            return "SUCCESS_AUDIO_PAUSE: Audio pausado en el kernel."
            
        elif accion_clean == "reproducir":
            # Envía la señal SIGCONT para reanudar el proceso congelado
            os.system("killall -SIGCONT mpv")
            return "SUCCESS_AUDIO_RESUME: Reanudando reproducción de fondo."
            
        return "Error: Comando multimedia no reconocido."
    except Exception as e:
        return f"Error en el controlador de audio: {str(e)}"