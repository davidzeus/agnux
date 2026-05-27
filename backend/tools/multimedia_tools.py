"""Herramientas multimedia para control de audio y reproducción en AGNUX."""

import subprocess
import os
from typing import Dict, Any


# Estado global del reproductor
_reproductor_estado = {
    "en_reproduccion": False,
    "cancion_actual": None,
    "volumen": 100,
}


def ejecutar_musica_fondo(archivo: str = None, volumen: int = 50) -> Dict[str, Any]:
    """
    Ejecuta música de fondo usando el reproductor del sistema.
    
    Args:
        archivo: Ruta del archivo de audio (opcional)
        volumen: Volumen de reproducción 0-100
    
    Returns:
        Dict con estado de la operación
    """
    global _reproductor_estado
    
    try:
        _reproductor_estado["volumen"] = volumen
        
        if archivo:
            if os.path.exists(archivo):
                _reproductor_estado["cancion_actual"] = archivo
                _reproductor_estado["en_reproduccion"] = True
                
                # Intenta usar paplay (PulseAudio)
                try:
                    subprocess.Popen(
                        ["paplay", "--volume", str(int(volumen * 655.36)), archivo],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                except FileNotFoundError:
                    # Fallback a mpg123
                    try:
                        subprocess.Popen(
                            ["mpg123", "-q", archivo],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    except FileNotFoundError:
                        return {
                            "estado": "ADVERTENCIA",
                            "resultado": "No hay reproductor de audio disponible",
                            "sugerencia": "Instala: apt install mpg123 o paplay"
                        }
                
                return {
                    "estado": "OK",
                    "reproduciendo": archivo,
                    "volumen": volumen
                }
            else:
                return {
                    "estado": "ERROR",
                    "resultado": f"Archivo no encontrado: {archivo}"
                }
        else:
            _reproductor_estado["en_reproduccion"] = True
            return {
                "estado": "OK",
                "resultado": "Música de fondo habilitada"
            }
    
    except Exception as e:
        return {
            "estado": "ERROR",
            "resultado": f"Error al reproducir música: {str(e)}"
        }


def controlar_reproductor_global(comando: str) -> Dict[str, Any]:
    """
    Controla el reproductor global de audio (pausar, reanudar, detener, siguiente, anterior).
    
    Args:
        comando: "pausar", "reanudar", "detener", "siguiente", "anterior"
    
    Returns:
        Dict con estado de la operación
    """
    global _reproductor_estado
    
    comando = comando.lower().strip()
    
    try:
        if comando == "pausar":
            _reproductor_estado["en_reproduccion"] = False
            return {
                "estado": "OK",
                "accion": "pausar",
                "resultado": "Reproducción pausada"
            }
        
        elif comando == "reanudar":
            _reproductor_estado["en_reproduccion"] = True
            return {
                "estado": "OK",
                "accion": "reanudar",
                "resultado": "Reproducción reanudada"
            }
        
        elif comando == "detener":
            _reproductor_estado["en_reproduccion"] = False
            _reproductor_estado["cancion_actual"] = None
            # Intenta detener todos los reproductores
            try:
                subprocess.run(["pkill", "-f", "paplay"], capture_output=True)
                subprocess.run(["pkill", "-f", "mpg123"], capture_output=True)
            except:
                pass
            return {
                "estado": "OK",
                "accion": "detener",
                "resultado": "Reproducción detenida"
            }
        
        elif comando == "siguiente":
            return {
                "estado": "INFO",
                "accion": "siguiente",
                "resultado": "Saltando a siguiente tema..."
            }
        
        elif comando == "anterior":
            return {
                "estado": "INFO",
                "accion": "anterior",
                "resultado": "Regresando al tema anterior..."
            }
        
        elif comando == "estado":
            return {
                "estado": "OK",
                "en_reproduccion": _reproductor_estado["en_reproduccion"],
                "cancion_actual": _reproductor_estado["cancion_actual"],
                "volumen": _reproductor_estado["volumen"]
            }
        
        else:
            return {
                "estado": "ERROR",
                "resultado": f"Comando no reconocido: {comando}"
            }
    
    except Exception as e:
        return {
            "estado": "ERROR",
            "resultado": f"Error al controlar reproductor: {str(e)}"
        }
