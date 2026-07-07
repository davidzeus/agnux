# Herramienta autogenerada de referencia: formato canónico de dynamicTools/.
# Cada archivo define funciones puras con type hints y docstring (descripción
# + Args); el Kernel las carga al arrancar y tras cada inyección.

def saludo(nombre: str = "mundo") -> str:
    """
    Devuelve un saludo personalizado del Kernel de AGNUX.
    Args:
        nombre: Nombre de la persona o entidad a saludar.
    """
    return f"Hola, {nombre}. Soy el Kernel cognitivo de AGNUX OS."
