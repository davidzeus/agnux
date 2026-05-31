from fastapi import APIRouter
from tools.system_tools import obtener_diagnostico_hardware, gestionar_energia_equipo

router = APIRouter()

@router.get("/status")
def get_system_status():
    """
    Retorna el estado de hardware y energía de forma instantánea.
    Ideal para tooltips en el frontend.
    """
    hw_info = obtener_diagnostico_hardware()
    bat_info = gestionar_energia_equipo("estado")
    
    return {
        "status": "ok",
        "hardware": hw_info,
        "power": bat_info
    }
