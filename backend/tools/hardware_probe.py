# tools/hardware_probe.py
import subprocess
import json
import os

PROFILE_PATH = "./system_profile.json"

def auto_evaluar_hardware_host() -> dict:
    """
    Censa las características de los componentes físicos del host Linux y despliega 
    el interrogatorio interactivo para balancear la carga de IA local o externa.
    """
    perfil = {
        "cpu_modelo": "Desconocido",
        "cpu_nucleos": 2,
        "ram_total_gb": 4,
        "posee_gpu_nvidia": False,
        "proveedor_ia": "local",        # 'local', 'gemini', 'openai'
        "modelo_ia_sugerido": "qwen2.5:1.5b",
        "teclado_layout": "us",
        "disco_raiz_libre_gb": 0,
        "api_key_guardada": ""
    }
    
    try:
        # 1. Análisis estructural de CPU
        perfil["cpu_modelo"] = subprocess.getoutput("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2").strip()
        perfil["cpu_nucleos"] = int(subprocess.getoutput("nproc"))

        # 2. Análisis de Memoria Física RAM
        with open("/proc/meminfo", "r") as f:
            for linea in f:
                if "MemTotal" in linea:
                    ram_kb = int(linea.split()[1])
                    perfil["ram_total_gb"] = round(ram_kb / (1024 * 1024))
                    break

        # 3. INTERFAZ INTERACTIVA PARA EL USUARIO EN EL BOOT
        print("\n" + "="*60)
        print(" 🌐 CONFIGURACIÓN DEL MOTOR DE INTELIGENCIA DE AGNUX")
        print("="*60)
        print(" Podés usar el procesamiento local en tu procesador o")
        print(" delegar la carga a la nube si poseés una suscripción.")
        print(" ⚠️ ¡ATENCIÓN!: El uso de la nube CONSUMIRÁ TOKENS de tu cuenta.")
        print("="*60)
        
        opcion = input("¿Deseás activar una suscripción externa via API Key? (si/no): ").strip().lower()
        
        if opcion in ["si", "s", "yes"]:
            print("\n Seleccioná el proveedor externo de tu preferencia:")
            print(" [1] Google Gemini (Modelo sugerido: gemini-2.5-flash)")
            print(" [2] OpenAI ChatGPT (Modelo sugerido: gpt-4o-mini)")
            prov_opcion = input(" Elección (1 o 2): ").strip()
            
            if prov_opcion == "1":
                key = input(" 🔑 Introducí tu GEMINI_API_KEY: ").strip()
                if key:
                    perfil["proveedor_ia"] = "gemini"
                    perfil["modelo_ia_sugerido"] = "gemini-2.5-flash"
                    perfil["api_key_guardada"] = key
                    os.environ["GEMINI_API_KEY"] = key
            elif prov_opcion == "2":
                key = input(" 🔑 Introducí tu OPENAI_API_KEY: ").strip()
                if key:
                    perfil["proveedor_ia"] = "openai"
                    perfil["modelo_ia_sugerido"] = "gpt-4o-mini"
                    perfil["api_key_guardada"] = key
                    os.environ["OPENAI_API_KEY"] = key
                    
            if perfil["proveedor_ia"] != "local":
                print("\n Conmutación completa. Redireccionando matriz de inferencia...")
            else:
                print("\n Entrada vacía. El sistema se replegará a la CPU local.")
        else:
            print("\n Confirmado. Se usará el circuito local nativo de Ollama.")

        # 4. Asignación local automatizada si no se seleccionó nube
        if perfil["proveedor_ia"] == "local":
            check_gpu = subprocess.run("command -v nvidia-smi && nvidia-smi", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if check_gpu.returncode == 0 and b"failed" not in check_gpu.stderr:
                perfil["posee_gpu_nvidia"] = True
                perfil["modelo_ia_sugerido"] = "qwen-test:latest"
            else:
                perfil["posee_gpu_nvidia"] = False
                # Para procesadores básicos o menos de 12GB de RAM, el de 1.5B evita congelar la PC
                if perfil["cpu_nucleos"] <= 4 or perfil["ram_total_gb"] < 12:
                    perfil["modelo_ia_sugerido"] = "qwen2.5:1.5b"
                else:
                    perfil["modelo_ia_sugerido"] = "qwen-test:latest"

        # 5. Mapeo de periféricos y persistencia
        layout = subprocess.getoutput("localectl status | grep 'X11 Layout' | cut -d: -f2").strip()
        if layout: perfil["teclado_layout"] = layout
        statvfs = os.statvfs('/')
        perfil["disco_raiz_libre_gb"] = round((statvfs.f_bavail * statvfs.f_frsize) / (1024 ** 3))

        # Guardamos la radiografía para que la IA la consulte en caliente si quiere
        with open(PROFILE_PATH, "w") as f:
            json.dump(perfil, f, indent=4)
            
        print("="*60 + "\n")
        return perfil
        
    except Exception as e:
        print(f"⚠️ Falla crítica en subsistema de introspección: {e}")
        return perfil