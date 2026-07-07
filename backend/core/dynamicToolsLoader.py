import os
import inspect
import importlib.util
from core.config import kernelLogger, dynamicToolsDir

def cargarFuncionesDesdeArchivo(rutaArchivo: str) -> list:
    """
    Importa un módulo de dynamicTools/ y devuelve sus funciones públicas
    (las herramientas autogeneradas que define).
    """
    nombreBase = os.path.splitext(os.path.basename(rutaArchivo))[0]
    nombreModulo = f"agnuxDynamicTools.{nombreBase}"

    spec = importlib.util.spec_from_file_location(nombreModulo, rutaArchivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)

    funciones = []
    for nombre, funcion in inspect.getmembers(modulo, inspect.isfunction):
        # Solo funciones definidas en el propio módulo (no re-importadas)
        if not nombre.startswith("_") and funcion.__module__ == nombreModulo:
            funciones.append(funcion)
    return funciones

def cargarHerramientasDinamicas() -> list:
    """
    Escanea backend/dynamicTools/ y devuelve todas las herramientas
    autogeneradas por el Kernel listas para registrarse en el agente.
    Un archivo corrupto no debe tumbar el arranque: se loguea y se salta.
    """
    herramientas = []
    if not os.path.isdir(dynamicToolsDir):
        return herramientas

    for nombreArchivo in sorted(os.listdir(dynamicToolsDir)):
        if not nombreArchivo.endswith(".py") or nombreArchivo.startswith("_"):
            continue
        rutaArchivo = os.path.join(dynamicToolsDir, nombreArchivo)
        try:
            funciones = cargarFuncionesDesdeArchivo(rutaArchivo)
            herramientas.extend(funciones)
            if funciones:
                kernelLogger.info(
                    f"🧩 [DYNAMIC-TOOLS] Cargada(s) {[f.__name__ for f in funciones]} desde {nombreArchivo}"
                )
        except Exception as e:
            kernelLogger.error(f"❌ [DYNAMIC-TOOLS] Error cargando {nombreArchivo}: {e}")
    return herramientas
