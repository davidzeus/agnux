# AGNUX — Motor de Orquestación Agéntica Local

**AGNUX** es un motor de orquestación agéntica de bajo nivel diseñado para automatizar y controlar servicios del sistema operativo mediante modelos de Inteligencia Artificial locales (vía Ollama) con soporte híbrido para proveedores en la nube (Gemini, OpenAI).

## 🎯 Propósito

Proveer un núcleo (core) agnóstico capaz de:
- Exponer una **API HTTP** y **WebSocket** para recibir prompts e inyectar inteligencia en aplicaciones.
- Invocar herramientas del sistema (diagnóstico, energía, multimedia).
- **Recargar dinámicamente** nuevas herramientas en caliente sin reiniciar.
- Funcionar como **demonio del sistema** con autonomía cognitiva.
- Escalar hacia un OS Linux completo gestionado por IA.

## ⚠️ Advertencia de Seguridad

Este proyecto incluye funcionalidades que **pueden controlar la energía del equipo** y **ejecutar procesos del sistema**. Revise cuidadosamente el código antes de ejecutarlo en producción. Los comandos de `shutdown`/`reboot` están **deshabilitados por defecto** en el backend seguro.

## 🏗️ Arquitectura y Características

- **Backend FastAPI** (`backend/app.py`): Orquestador cognoscitivo unificado con soporte multi-proveedor.
- **Agente agnóstico** (`backend/agent_core.py`): Configuración flexible con Ollama local, Gemini o OpenAI.
- **Subsistemas de herramientas**: Diagnóstico, multimedia, energía e inyección dinámica de scripts.
- **Frontend Angular** (`frontend/`): Interfaz moderna para interactuar con el kernel.
- **Autogénesis**: Capacidad de crear nuevas herramientas automáticamente cuando el usuario lo requiere.
- **Failover inteligente**: Si la nube pincha, replica automáticamente a Ollama local.
- **Telemetría**: Registro de consumo de tokens en el backend local (`dynamic_tools/historial_consumo.json`).

## 📁 Estructura del Repositorio

```
agnux/
├── backend/
│   ├── app.py                          # Servidor FastAPI (orquestador principal)
│   ├── agent_core.py                   # Configuración del agente con IA multi-proveedor
│   ├── system_profile.json             # Perfil del sistema (proveedor, modelo, API keys)
│   ├── tools/
│   │   ├── system_tools.py             # Herramientas de diagnóstico y energía (seguras)
│   │   └── multimedia_tools.py         # Control de reproducción multimedia
│   └── dynamic_tools/                  # Herramientas autogeneradas en caliente
│       ├── __init__.py
│       ├── historial_consumo.json      # Telemetría de consumo de tokens
│       └── *.py                        # Scripts inyectados dinámicamente
├── frontend/
│   ├── package.json
│   ├── angular.json
│   ├── src/
│   │   ├── main.ts                     # Punto de entrada
│   │   ├── main.server.ts              # SSR
│   │   ├── app.component.ts            # Componente raíz
│   │   ├── components/
│   │   │   └── command-bar/            # Barra de comandos
│   │   └── services/
│   │       └── agnux.service.ts        # Cliente HTTP/WebSocket
│   └── assets/
├── requirements.txt                    # Dependencias Python
└── README.md                           # Este archivo
```

## 🚀 Instalación Rápida

### Requisitos Previos

**Sistema Operativo**: Linux (Ubuntu/Debian/Fedora)

**Software requerido**:
- Python 3.9+
- Node.js 18+ (para el frontend)
- **Ollama** (para IA local) — [Descargar](https://ollama.ai)
- MPV, MPG123 o PulseAudio (para multimedia)

### 1️⃣ Configurar Ollama Local

**Ollama** es el runtime que ejecuta modelos de IA localmente sin depender de APIs en la nube.

#### Instalar Ollama:

```bash
# En Linux (Ubuntu/Debian):
curl -fsSL https://ollama.ai/install.sh | sh

# O descargar desde: https://ollama.ai/download
```

#### Iniciar Ollama como servicio:

```bash
# Ollama se ejecuta como daemon en puerto 11434
ollama serve

# En otra terminal, descargar un modelo (ej: qwen2.5:1.5b):
ollama pull qwen2.5:1.5b
ollama pull mistral
ollama pull neural-chat
```

**Modelos recomendados** para AGNUX:
- `qwen2.5:1.5b` (rápido, eficiente) ⚡
- `mistral` (mejor calidad, más recursos)
- `neural-chat` (optimizado para chat)

### 2️⃣ Configurar el Entorno Python

```bash
# Navegar al directorio del proyecto
cd /home/david/Documentos/agnux

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

### 3️⃣ Configurar Variables de Entorno

Las variables de entorno controlan qué proveedor de IA usa AGNUX. Crea un archivo `.env` en la raíz:

```bash
# .env — Variables de Entorno para AGNUX
# ================================================

# ⚡ PROVEEDOR DE IA (local, gemini, openai)
AGNUX_IA_PROVIDER=local

# 🧠 MODELO A USAR (debe estar disponible en Ollama si es local)
AGNUX_ACTIVE_MODEL=qwen2.5:1.5b

# 🌐 SOLO PARA GEMINI (si AGNUX_IA_PROVIDER=gemini)
GEMINI_API_KEY=tu-api-key-aqui

# 🔑 SOLO PARA OPENAI (si AGNUX_IA_PROVIDER=openai)
OPENAI_API_KEY=sk-...

# 🏠 URL LOCAL DE OLLAMA (por defecto: http://127.0.0.1:11434)
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

#### Ejemplo 1: Usando Ollama Local (RECOMENDADO)

```bash
export AGNUX_IA_PROVIDER=local
export AGNUX_ACTIVE_MODEL=qwen2.5:1.5b
```

Luego ejecuta en la terminal:
```bash
cd backend
python3 -m uvicorn app:app --reload --port 8000
```

**Verificar que Ollama está corriendo**:
```bash
curl http://127.0.0.1:11434/api/tags
```

#### Ejemplo 2: Usando Gemini (Nube con Failover a Ollama)

```bash
export AGNUX_IA_PROVIDER=gemini
export AGNUX_ACTIVE_MODEL=gemini-2.5-flash
export GEMINI_API_KEY=AIzaSy...
```

Si la API de Gemini falla o no hay conexión, **AGNUX automáticamente replica a Ollama local**.

### 4️⃣ Ejecutar el Backend

```bash
cd backend

# Con recarga automática (desarrollo)
AGNUX_IA_PROVIDER=local AGNUX_ACTIVE_MODEL=qwen2.5:1.5b \
  python3 -m uvicorn app:app --reload --port 8000

# Producción (sin recarga)
AGNUX_IA_PROVIDER=local python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

**Logs esperados**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
🔍 AGNUX INITIAL BOOT: Configurando entorno...
🚀 NÚCLEO CONFIGURADO -> Runtime: local
```

### 5️⃣ Ejecutar el Frontend (Angular)

```bash
cd frontend
npm install
npm start
```

Acceder en: **http://localhost:4200**

## 📡 API Endpoints

### POST `/api/system/intent`

Envía un prompt al kernel agnóstico.

**Request**:
```bash
curl -X POST http://localhost:8000/api/system/intent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "¿Cuál es el estado de mi hardware?"}'
```

**Response**:
```json
{
  "status": "success",
  "user": "user_cristian",
  "response": "{\"cpu_percent\": 45.2, \"memory_percent\": 62.1, \"disk_percent\": 78.5}"
}
```

### WebSocket `/ws/system-events`

Recibe eventos del sistema en tiempo real (se agregará pronto).

## 🧠 Herramientas Disponibles

| Herramienta | Descripción |
|---|---|
| `tool_diagnostico_wrapper` | Estado del hardware (CPU, RAM, disco) |
| `tool_reproductor_video` | Reproducción de videos locales o YouTube |
| `tool_musica_wrapper` | Reproducción de música de fondo |
| `tool_control_audio_wrapper` | Control de reproducción (pausa, resume, detiene) |
| `autogenerar_nueva_tool` | Crea nuevas herramientas dinámicamente |

## 🔧 Desarrollo y Extensión

### Crear una Herramienta Dinámica

El agente puede crear automáticamente nuevas herramientas si las necesita. Si envías un prompt como:

```
"Crea una herramienta que liste todos los archivos .mp3 en mi home"
```

El agente invocará `autogenerar_nueva_tool` y creará un script en `backend/dynamic_tools/` que se cargará automáticamente.

### Agregar una Herramienta Manualmente

1. Crear archivo en `backend/dynamic_tools/mi_herramienta.py`:

```python
"""Descripción de mi herramienta"""

def mi_herramienta():
    """Realiza una tarea específica"""
    return "Resultado de la tarea"
```

2. Reiniciar el backend (o esperar a que el agente llame a `recargar_herramientas_dinamicas()`).

## 🔍 Depuración

### Ver Logs del Backend

```bash
tail -f /tmp/agnux.log  # Si lo configuras con logging a archivo
```

### Probar Ollama

```bash
# ¿Está Ollama corriendo?
curl http://127.0.0.1:11434/api/tags

# Probar un modelo
curl http://127.0.0.1:11434/api/generate \
  -d '{"model": "qwen2.5:1.5b", "prompt": "Hola", "stream": false}'
```

### Problemas Comunes

| Problema | Solución |
|---|---|
| `Connection refused: http://127.0.0.1:11434` | Ollama no está corriendo. Ejecuta `ollama serve` en otra terminal. |
| `Model not found: qwen2.5:1.5b` | Descarga el modelo: `ollama pull qwen2.5:1.5b` |
| `No module named 'agno'` | Instala dependencias: `pip install -r requirements.txt` |
| Frontend no se conecta al backend | Verifica que el backend esté en `http://localhost:8000` y CORS habilitado. |

## 📊 Monitoreo de Consumo (Gemini)

Si usas Gemini, el consumo de tokens se registra en `backend/dynamic_tools/historial_consumo.json`:

```json
[
  {
    "fecha": "2025-05-27 14:32:10",
    "prompt": "¿Cuál es el estado del hardware?",
    "prompt_tokens": 145,
    "candidates_tokens": 89,
    "total_tokens": 234
  }
]
```

## 🎯 Roadmap

- [ ] WebSocket para eventos del sistema en tiempo real
- [ ] Panel de administración en el frontend
- [ ] Autenticación y autorización
- [ ] Soporte para GPT-4o local (LM Studio)
- [ ] Integración con Telegram/Discord
- [ ] Empaquetamiento como systemd service
- [ ] Migración a kernel Linux customizado (Fase 2)

## 📝 Contribución

Si encuentras bugs o tienes mejoras:

1. Abre un **issue** describiendo el problema
2. Crea un **PR** con cambios enfocados y documentados
3. Mantén el código limpio y los módulos desacoplados

## ⚙️ Configuración Avanzada

### Cambiar Puerto del Backend

```bash
python3 -m uvicorn app:app --port 9000
```

### Cambiar Modelo en Tiempo de Ejecución

```bash
export AGNUX_ACTIVE_MODEL=mistral
python3 -m uvicorn app:app --reload
```

### Usar Múltiples Modelos

En `backend/app.py` puedes agregar lógica para seleccionar modelos por contexto (p. ej., modelos pesados para análisis, ligeros para chat).

## 📧 Contacto y Soporte

Para preguntas técnicas sobre:
- Integración de Ollama: revisa [Ollama Docs](https://github.com/ollama/ollama)
- API de AGNUX: consulta `backend/app.py`
- Frontend Angular: revisa `frontend/README.md`

---

**Versión**: 1.0.0 | **Última actualización**: Mayo 2025 | **License**: MIT (agregar LICENSE.md)
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
