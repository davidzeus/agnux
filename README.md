# AGNUX

AGNUX es un motor de orquestación agéntica de bajo nivel y lógica industrial diseñado para automatizar y controlar servicios del sistema operativo mediante modelos de Inteligencia Artificial locales y distribuidos.

**Propósito:** Proveer un núcleo (core) capaz de exponer una API y un agente agnóstico que puede invocar herramientas del sistema, gestionar dispositivos y reproducir multimedia, además de inyectar nuevas herramientas en caliente.

**Advertencia de seguridad:** Este proyecto incluye funcionalidades que pueden controlar la energía del equipo y ejecutar procesos del sistema. Revise cuidadosamente los controladores de energía y las llamadas a `shutdown`/`reboot` antes de ejecutarlo en un equipo de producción.

**Características principales:**
- **Agente agnóstico** con integración a modelos locales (via Ollama) — ver `backend/agent_core.py`.
- **API HTTP + WebSocket** para recibir prompts y emitir eventos — ver `backend/app.py`.
- **Subsistemas de herramientas** para diagnóstico, energía y multimedia (hot-reload en `dynamic_tools`).
- **Autogénesis de herramientas**: posibilidad de inyectar scripts Python en `backend/dynamic_tools/`.

**Estructura del repositorio**
- [backend/app.py](backend/app.py): Servidor FastAPI que expone endpoints y WebSocket.
- [backend/agent_core.py](backend/agent_core.py): Configuración del agente, wrappers de herramientas y motor de recarga dinámica.
- [backend/tools/system_tools.py](backend/tools/system_tools.py): Herramientas de diagnóstico y gestión (seguras / simuladas).
- [backend/tools/multimedia_tools.py](backend/tools/multimedia_tools.py): Reproducción y control multimedia a nivel de sistema.
- [tools/system_tools.py](tools/system_tools.py): Implementación alternativa de utilidades (incluye comandos destructivos si se usan directamente).
- [tools/multimedia_tools.py](tools/multimedia_tools.py): Control de MPV / reproducción vía ytdl.
- `requirements.txt`: dependencias del proyecto.

Instalación y entorno
---------------------
Se asume un sistema Linux (las herramientas usan utilidades como `mpv`, `mpg123`, `paplay`, `pkill`, etc.).

1. Crear y activar un entorno virtual (recomendado):

```bash
cd /home/david/Documentos/agnux
python3 -m venv .venv
source .venv/bin/activate
```

2. Instalar dependencias:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Notas sobre dependencias notables:
- `ollama` y el uso de modelos locales: requiere que tenga Ollama instalado y modelos cargados localmente si quiere ejecutar el agente con backend Ollama.
- `chromadb`, `opencv-python-headless`, `psutil` son usados por módulos de análisis y multimedia.

Ejecución (desarrollo)
----------------------
Para ejecutar la API de desarrollo desde el directorio `backend`:

```bash
cd backend
# Ejecuta con autoreload en puerto 8000 (dev)
python3 -m uvicorn app:app --reload --port 8000
```

El endpoint principal para enviar prompts es `POST /api/system/intent` (ver `backend/app.py`). También hay un WebSocket en `/ws/system-events` para eventos del sistema.

Comportamiento del agente y herramientas
---------------------------------------
- El agente se configura en `backend/agent_core.py` usando `agno.agent.Agent` y el conector `agno.models.ollama.Ollama`.
- Las funciones expuestas como herramientas (diagnóstico, energía, multimedia) tienen wrappers con tipado y son registradas en el agente. El motor puede recargar scripts Python almacenados en `backend/dynamic_tools/` en caliente.
- Atención especial a la gestión de energía:
  - `backend/tools/system_tools.py` retorna mensajes de advertencia y no ejecuta apagados por seguridad (ver el código). En cambio, `tools/system_tools.py` en el nivel superior contiene llamadas directas a `shutdown`/`reboot` si se invocan; no llame a esas funciones sin revisar el código.

Desarrollo y extensión
----------------------
- Para añadir una herramienta en caliente desde el propio agente use la función `autogenerar_nueva_tool` en `backend/agent_core.py` (escribe un archivo `.py` en `backend/dynamic_tools/`).
- Después de añadir el archivo, el endpoint que llame a `recargar_herramientas_dinamicas()` actualizará las herramientas disponibles.

Depuración
---------
- Logs: `backend/app.py` configura logging básico y muestra actividad del núcleo y tiempos de respuesta.
- Si el agente falla al hablar con el runtime de modelos, revise que Ollama (u otro backend) esté corriendo y accesible.

Recomendaciones operativas
--------------------------
- Ejecute primero en una máquina de pruebas o VM antes de habilitar en hardware crítico.
- Verifique y adapte los comandos de reproducción y control de audio según su distribución (PulseAudio, PipeWire, MPV instalados).
- Si no desea que el sistema ejecute `shutdown` o `reboot`, deje las funciones de energía en modo simulación o comente las llamadas peligrosas.

Contribución
------------
Si desea colaborar, abra issues o PR con mejoras específicas. Mantenga cambios aislados por módulos y documente cualquier comando del sistema que agregue.

Licencia
--------
Agregue aquí la licencia elegida para su proyecto.

Contacto
-------
Para preguntas técnicas sobre la integración del agente o despliegue local, revise los archivos mencionados arriba y abra un issue en este repositorio.

**Nota importante: objetivo — Ejecutar sobre un kernel Linux como un OS completo**
------------------------------------------------------------------
La intención del proyecto es evolucionar AGNUX desde un servicio de usuario a un sistema operativo completo construido sobre un kernel Linux. A continuación hay pautas técnicas y opciones de implementación para alcanzar ese objetivo de forma segura y reproducible.

- **Estrategias de arquitectura (prioritarias):**
  - *Fase 1 (rápida, recomendada):* Ejecutar AGNUX como un demonio de espacio de usuario (daemon) gestionado por `systemd`. Esto permite control del sistema, integración con el arranque y permisos elevados sin tocar el kernel.
  - *Fase 2 (sistema integrado):* Empaquetar una imagen mínima del sistema con `debootstrap` o `buildroot` que arranque directamente con AGNUX como servicio crítico (o como `init` alternativo), adaptando `systemd` o un init ligero según necesidad.
  - *Fase 3 (núcleo extendido):* Si se requiere funcionalidad que exige espacio de kernel (drivers propietarios, hooks ACPI específicos), desarrollar módulos del kernel o parches específicos. Evitar el kernel siempre que sea posible por complejidad y riesgos.

- **Privilegios, seguridad y aislamiento:**
  - Evite ejecutar código arbitrario como `root`. Minimize privilegios usando *capabilities* (`cap_sys_admin`, etc.) y dropping de privilegios después del arranque.
  - Use `systemd` sandboxes (`PrivateTmp`, `ProtectSystem`, `NoNewPrivileges`) y perfiles `AppArmor`/`SELinux` para limitar el daño de herramientas dinámicas y cargas no confiables.
  - Proteja los puntos de ejecución de comandos sensibles (shutdown/reboot): mantenga modo simulación por defecto y requiera confirmación o un token seguro para acciones destructivas.

- **Ejemplo: unidad `systemd` para ejecutar AGNUX como servicio del sistema**

```
[Unit]
Description=AGNUX Core Agent
After=network.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/home/david/Documentos/agnux/backend
ExecStart=/home/david/Documentos/agnux/.venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=5
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
```

Guarde este fichero como `agnux.service` en `/etc/systemd/system/` y luego:

```bash
sudo systemctl daemon-reload
sudo systemctl enable agnux.service
sudo systemctl start agnux.service
sudo journalctl -u agnux.service -f
```

- **Construcción de una imagen mínima (opciones rápidas):**
  - *Debian/Ubuntu minimal ISO*: usar `debootstrap` para crear un chroot mínimo, instalar `systemd`, copiar AGNUX y sus dependencias, y generar una ISO de arranque con `grub`.
  - *Buildroot*: para imagenes más controladas y pequeñas, use `buildroot` y empaquete AGNUX en `/usr/bin` o como servicio.
  - *Contenedores/OCI images*: para pruebas y despliegues, empaquete AGNUX en una imagen Docker/OCI y ejecute sobre un host Linux o en máquinas virtuales.

- **Pruebas y despliegue seguro:**
  - Primero pruebe todo dentro de una VM (QEMU/KVM, VirtualBox) antes de instalar en hardware real.
  - Automatice instalaciones en VM usando cloud-init o scripts de `debootstrap` para reproducibilidad.

- **Recomendaciones prácticas:**
  - Mantenga separación clara entre código que necesita privilegios y lógica de alto nivel; use IPC o sockets UNIX para comunicación segura entre procesos con distinta privilegiación.
  - Documente cualquier comando del sistema que pueda afectar el hardware (apagar, reiniciar, manipular particiones) y pida confirmación explícita.
  - Use control de versiones y CI para construir imágenes y ejecutar pruebas en entornos emulados antes de desplegar en dispositivos reales.

Si quieres, actualizo el README con ejemplos concretos de `debootstrap` o un script de creación de imagen, o creo la unidad `systemd` y un script de empaquetado inicial para que lo pruebes en una VM. Indícame qué prefieres.
