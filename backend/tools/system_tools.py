"""Herramientas de diagnóstico y gestión del sistema para AGNUX."""

import os
import psutil
import platform
import subprocess
from typing import Dict, Any


def obtener_diagnostico_hardware() -> Dict[str, Any]:
    """
    Obtiene un diagnóstico completo del hardware del sistema.
    
    Returns:
        Dict con información de CPU, memoria, disco y otros componentes.
    """
    try:
        # Información del sistema
        info_sistema = {
            "plataforma": platform.system(),
            "arquitectura": platform.machine(),
            "procesador": platform.processor(),
            "version_python": platform.python_version(),
        }
        
        # CPU
        cpu_info = {
            "cantidad_nucleos": psutil.cpu_count(logical=False),
            "nucleos_logicos": psutil.cpu_count(logical=True),
            "uso_porcentaje": psutil.cpu_percent(interval=1),
            "frecuencia_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else 0,
        }
        
        # Memoria
        memoria = psutil.virtual_memory()
        mem_info = {
            "total_gb": round(memoria.total / (1024**3), 2),
            "disponible_gb": round(memoria.available / (1024**3), 2),
            "usado_gb": round(memoria.used / (1024**3), 2),
            "porcentaje_uso": memoria.percent,
        }
        
        # Disco
        disco = psutil.disk_usage('/')
        disco_info = {
            "total_gb": round(disco.total / (1024**3), 2),
            "disponible_gb": round(disco.free / (1024**3), 2),
            "usado_gb": round(disco.used / (1024**3), 2),
            "porcentaje_uso": disco.percent,
        }
        
        return {
            "estado": "OK",
            "sistema": info_sistema,
            "cpu": cpu_info,
            "memoria": mem_info,
            "disco": disco_info,
            "uptime_horas": round(psutil.boot_time() / 3600, 2)
        }
    except Exception as e:
        return {
            "estado": "ERROR",
            "mensaje": f"Error al obtener diagnóstico: {str(e)}"
        }


def gestionar_energia_equipo(accion: str = "estado") -> Dict[str, str]:
    """
    Gestiona la energía del equipo (apagar, reiniciar, suspender).
    
    Args:
        accion: "estado", "apagar", "reiniciar" o "suspender"
    
    Returns:
        Dict con el resultado de la operación
    """
    accion = accion.lower().strip()
    
    try:
        if accion == "estado":
            # Retorna información sobre el estado de energía
            bateria = psutil.sensors_battery()
            if bateria:
                return {
                    "estado": "CONECTADO" if bateria.power_plugged else "BATERÍA",
                    "porcentaje": f"{bateria.percent}%",
                    "tiempo_restante": f"{bateria.secsleft // 3600}h {(bateria.secsleft % 3600) // 60}m"
                }
            else:
                return {
                    "estado": "AC_CONECTADO",
                    "info": "Sistema de escritorio sin batería"
                }
        
        elif accion == "apagar":
            # Solo simula, no ejecuta comando real por seguridad
            return {
                "estado": "ADVERTENCIA",
                "accion": "apagar",
                "resultado": "Comando no ejecutado por razones de seguridad. Usa: sudo shutdown -h now"
            }
        
        elif accion == "reiniciar":
            return {
                "estado": "ADVERTENCIA",
                "accion": "reiniciar",
                "resultado": "Comando no ejecutado por razones de seguridad. Usa: sudo reboot"
            }
        
        elif accion == "suspender":
            return {
                "estado": "ADVERTENCIA",
                "accion": "suspender",
                "resultado": "Comando no ejecutado. Usa: systemctl suspend"
            }
        
        else:
            return {
                "estado": "ERROR",
                "resultado": f"Acción no reconocida: {accion}"
            }
    
    except Exception as e:
        return {
            "estado": "ERROR",
            "resultado": f"Error al gestionar energía: {str(e)}"
        }
