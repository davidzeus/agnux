import subprocess
import os

def obtener_diagnostico_hardware() -> str:
    """
    Lee la telemetria real del hardware del equipo en Linux (Uso de CPU, RAM y almacenamiento).
    Devuelve un reporte limpio y humano sobre el estado de los recursos.
    """
    try:
        # 1. Obtener uso de Memoria RAM ( parsing de 'free -m' )
        # Extraemos la memoria total, usada y disponible en Megabytes
        comando_ram = "free -m | grep Mem:"
        linea_ram = subprocess.getoutput(comando_ram).split()
        ram_total = linea_ram
        ram_usada = linea_ram
        ram_libre = linea_ram # memoria disponible real
        
        # 2. Obtener uso del Disco Duro principal ( parsing de 'df -h' )
        # Monitoreamos la partición raíz del sistema operativo
        comando_disco = "df -h / | tail -1"
        linea_disco = subprocess.getoutput(comando_disco).split()
        disco_total = linea_disco
        disco_usado = linea_disco
        disco_disponible = linea_disco
        disco_porcentaje = linea_disco
        
        # 3. Obtener carga promedio de la CPU ( parsing de '/proc/loadavg' )
        # Lee la carga de trabajo en el último minuto, 5 minutos y 15 minutos
        with open("/proc/loadavg", "r") as f:
            load_avg = f.read().split()[:3]
        cpu_carga = f"1 min: {load_avg} | 5 min: {load_avg} | 15 min: {load_avg}"

        # Maquetamos el reporte estructurado
        reporte = (
            f"📊 --- DIAGNÓSTICO DE HARDWARE AGNUX ---\n"
            f"🧠 CPU (Carga promedio) -> {cpu_carga}\n"
            f"💾 Memoria RAM -> Total: {ram_total}MB | Usada: {ram_usada}MB | Disponible: {ram_libre}MB\n"
            f"💽 Disco Principal -> Total: {disco_total} | Usado: {disco_usado} ({disco_porcentaje}) | Libre: {disco_disponible}\n"
            f"----------------------------------------"
        )
        return reporte

    except Exception as e:
        return f"Error crítico al interrogar las métricas del Kernel: {str(e)}"

def gestionar_energia_equipo(accion: str) -> str:
    """
    Controla el estado de energia físico de la computadora de forma nativa.
    :param accion: Valores aceptados: 'apagar', 'reiniciar'.
    """
    accion_clean = accion.lower().strip()
    
    if accion_clean == "apagar":
        # Usamos Popen para desvincular el proceso y que de tiempo a responder a la API
        subprocess.Popen("shutdown -h now", shell=True)
        return "SUCCESS_POWEROFF: AGNUX ha enviado la señal ACPI de apagado al hardware."
        
    elif accion_clean == "reiniciar":
        subprocess.Popen("reboot", shell=True)
        return "SUCCESS_REBOOT: Reiniciando el sistema operativo..."
        
    return "Error: Acción de energía no reconocida por el controlador."             