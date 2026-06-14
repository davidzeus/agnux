import platform
import time
import psutil
from fastapi import APIRouter
from typing import Dict, Any
from core.config import aiStats

router = APIRouter()

def obtenerDiagnosticoHardware() -> Dict[str, Any]:
    """
    Obtiene un diagnóstico completo del hardware del sistema.
    """
    try:
        infoSistema = {
            "plataforma": platform.system(),
            "arquitectura": platform.machine(),
            "procesador": platform.processor(),
            "versionPython": platform.python_version(),
        }
        
        cpuFreq = psutil.cpu_freq()
        cpuInfo = {
            "cantidadNucleos": psutil.cpu_count(logical=False),
            "nucleosLogicos": psutil.cpu_count(logical=True),
            "usoPorcentaje": psutil.cpu_percent(interval=0.1),
            "frecuenciaMhz": cpuFreq.current if cpuFreq else 0,
        }
        
        memoria = psutil.virtual_memory()
        memInfo = {
            "totalGb": round(memoria.total / (1024**3), 2),
            "disponibleGb": round(memoria.available / (1024**3), 2),
            "usadoGb": round(memoria.used / (1024**3), 2),
            "porcentajeUso": memoria.percent,
        }
        
        disco = psutil.disk_usage('/')
        discoInfo = {
            "totalGb": round(disco.total / (1024**3), 2),
            "disponibleGb": round(disco.free / (1024**3), 2),
            "usadoGb": round(disco.used / (1024**3), 2),
            "porcentajeUso": disco.percent,
        }
        
        return {
            "estado": "OK",
            "sistema": infoSistema,
            "cpu": cpuInfo,
            "memoria": memInfo,
            "disco": discoInfo,
            "uptimeHoras": round((time.time() - psutil.boot_time()) / 3600, 2)
        }
    except Exception as e:
        return {
            "estado": "ERROR",
            "mensaje": f"Error al obtener diagnóstico: {str(e)}"
        }

def gestionarEnergiaEquipo(accion: str = "estado") -> Dict[str, str]:
    """
    Gestiona la energía del equipo (apagar, reiniciar, suspender).
    """
    accionClean = accion.lower().strip()
    try:
        if accionClean == "estado":
            bateria = psutil.sensors_battery()
            if bateria:
                return {
                    "estado": "CONECTADO" if bateria.power_plugged else "BATERÍA",
                    "porcentaje": f"{bateria.percent}%",
                    "tiempoRestante": f"{bateria.secsleft // 3600}h {(bateria.secsleft % 3600) // 60}m"
                }
            else:
                return {
                    "estado": "AC_CONECTADO",
                    "info": "Sistema de escritorio sin batería"
                }
        elif accionClean in ["apagar", "reiniciar", "suspender"]:
            return {
                "estado": "ADVERTENCIA",
                "accion": accionClean,
                "resultado": f"Comando {accionClean} no ejecutado por seguridad en entorno web."
            }
        else:
            return {
                "estado": "ERROR",
                "resultado": f"Acción no reconocida: {accionClean}"
            }
    except Exception as e:
        return {
            "estado": "ERROR",
            "resultado": f"Error al gestionar energía: {str(e)}"
        }

@router.get("/status")
def getSystemStatus():
    """
    Retorna el estado de hardware y energía de forma instantánea.
    """
    hwInfo = obtenerDiagnosticoHardware()
    batInfo = gestionarEnergiaEquipo("estado")
    
    return {
        "status": "ok",
        "hardware": hwInfo,
        "power": batInfo,
        "aiStats": aiStats
    }
