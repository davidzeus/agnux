"""
Definición autogenerada por AGNUX OS Core.
"""

def listar_descargas():
    """Muestra una lista de los archivos en la carpeta de descargas del usuario."""

    import os

    try:
        downloads_path = os.path.expanduser("~/Descargas")
        files = os.listdir(downloads_path)
        if files:
            return "Archivos en tus descargas:\n" + "\n".join(files)
        else:
            return "No hay archivos en tu carpeta de descargas."
    except FileNotFoundError:
        return "La carpeta de descargas no fue encontrada."
    except Exception as e:
        return f"Ocurrió un error al listar descargas: {e}"
    
