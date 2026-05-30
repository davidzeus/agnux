<div align="center">
  <h1>🧠 AGNUX OS</h1>
  <p><strong>Un Sistema Operativo Cognitivo y Autónomo impulsado por IA, Metaprogramación y Biometría</strong></p>
  
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
  [![Angular](https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white)](https://angular.io/)
  [![Ollama](https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=Ollama&logoColor=white)](https://ollama.ai/)
  [![Qdrant](https://img.shields.io/badge/Qdrant-FF5252?style=for-the-badge&logo=qdrant&logoColor=white)](https://qdrant.tech/)
</div>

---

**AGNUX OS** no es simplemente un asistente virtual; es una arquitectura de **Kernel Cognitivo** diseñada para gobernar hardware, interfaces de usuario y bases de datos mediante el razonamiento semántico de grandes modelos de lenguaje (LLMs). AGNUX está diseñado para correr en servidores de alto rendimiento (ej. *Lenovo SR630*) y actuar como el cerebro maestro de múltiples terminales conectadas vía red o VPN (WireGuard).

## ✨ Características Principales

### 🧬 Autogénesis (Metaprogramación en Caliente)
AGNUX tiene la capacidad de **escribir su propio código** en tiempo real. Cuando el Agente detecta una intención del usuario que no puede resolver con sus herramientas estáticas, genera un script en Python, lo guarda en el host (`dynamic_tools/`), lo compila en memoria y lo ejecuta instantáneamente sin requerir reinicios del servidor.

### 👁️ Biometría y Bypass VPN (Control de Acceso)
El sistema incluye un módulo de autenticación de doble vía:
- **Biometría Facial/Vocal**: Análisis vectorial (128d) contra perfiles de usuario.
- **Bypass Remoto Móvil**: Permite que un operador autenticado desde su teléfono móvil (conectado vía WireGuard VPN) desbloquee de forma remota una terminal física (monitor ciego) mediante túneles SSE.

### 🧠 Memoria Episódica y Router Semántico (Omnisciencia)
- **Qdrant Vector DB**: Toda interacción, ejecución de herramienta o registro biométrico se vectoriza (`SentenceTransformer: paraphrase-multilingual-mpnet-base-v2`, 768d) y se guarda en colecciones persistentes.
- **Recuperación de Contexto**: En cada prompt, AGNUX inyecta automáticamente los recuerdos más relevantes del usuario para mantener una ilusión de omnisciencia real.
- **Multiplexación Jerárquica**: Los perfiles de memoria e intenciones de red están rígidamente normalizados usando estándares de Kernel Linux (RFC 1035, usando únicamente guiones medios `-`).

### ⚡ Event-Driven UI (HyperIsland & Kiosco)
El backend y frontend (Angular 15+) se comunican estrictamente mediante flujos asíncronos unidireccionales (**SSE - Server-Sent Events**) y **WebSockets**.
- **Ventanas Dinámicas**: El Kernel puede emitir eventos `CREATE_WINDOW` para dibujar contenedores flotantes en el escritorio del cliente.
- **Ejecución en Host**: El Kernel puede controlar el hardware (encendido/apagado), reproducir audio de fondo, cambiar fondos de escritorio o abrir contenedores Kiosco (Chromium para Netflix, Spotify, etc).

---

## 🏗️ Arquitectura del Sistema

El backend ha sido refactorizado recientemente usando un diseño de micro-módulos para garantizar la mantenibilidad y escalabilidad en FastAPI.

```text
backend/
├── main.py                  # Entrypoint de FastAPI y Middlewares (CORS)
├── core/
│   ├── config.py            # Variables de entorno y dependencias globales (.env)
│   └── memory.py            # Instancia de Qdrant y CACHE_VECTORS en RAM
├── schemas/
│   └── models.py            # Entidades Pydantic (Validación estricta de payloads)
├── services/
│   ├── intent_orchestrator.py # Motor iterador asíncrono con Ollama (El "Cerebro")
│   └── tools_service.py     # Gestor de autogénesis y subprocesos del host
├── api/
│   └── routes/
│       ├── intent.py        # Websockets e inferencia de flujos
│       └── auth.py          # Endpoints de enrolamiento y bypass biométrico
├── dynamic_tools/           # (Directorio de scripts auto-generados por IA)
└── tools/                   # (Herramientas estáticas del host)
```

---

## 🚀 Requisitos y Configuración Inicial

> [!NOTE]
> **Estado de Despliegue**: Actualmente, el ecosistema backend está dockerizado para facilitar el desarrollo rápido y asegurar consistencia entre colaboradores. Sin embargo, **el objetivo arquitectónico final es montarlo de forma nativa directamente sobre un Kernel Linux (bare-metal)** para maximizar la ejecución de subprocesos de bajo nivel y el control absoluto del hardware.

### Hardware Recomendado (Entorno Base de Referencia)
Dado que AGNUX opera con modelos LLM locales en caliente y modelos de embeddings en RAM, se requiere hardware robusto para una experiencia fluida. La configuración actual de desarrollo recomendada es:
- **GPU**: NVIDIA RTX 5070 (12GB VRAM) *[Para inferencia ágil de Ollama]*
- **CPU**: Intel Core i7-12700F (o procesador equivalente multi-núcleo)
- **RAM**: 64GB DDR4 *[Para absorción de buffers, matrices vectoriales en memoria y metaprogramación concurrente]*

### Prerrequisitos
- **Python 3.11+**
- **Docker** (Entorno de desarrollo actual)
- **Node.js 18+** y **Angular CLI 15+** (Para el cliente)
- Nodos independientes u hospedados de:
  - **Ollama** (Recomendado: `ministral-es:latest` para razonamiento y `deepseek-coder` para herramientas).
  - **Qdrant DB** (Expuesto en el puerto 6333).

### Configuración del Backend

1. **Clonar y preparar entorno:**
   ```bash
   cd agnux/backend
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Variables de Entorno (`backend/.env`):**
   Crea un archivo `.env` en el directorio `backend` con la siguiente estructura:
   ```env
   OLLAMA_HOST=http://<IP_NODO_OLLAMA>:11434
   QDRANT_HOST=http://<IP_NODO_QDRANT>:6333
   AGNUX_ACTIVE_MODEL=ministral-es:latest
   AGNUX_CODER_MODEL=deepseek-coder:1.5b
   ```

3. **Ejecutar el Kernel:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Configuración del Frontend (Angular)

1. **Instalar dependencias:**
   ```bash
   cd agnux/frontend
   npm install
   ```

2. **Ejecutar el cliente:**
   ```bash
   ng serve --host 0.0.0.0 --port 4200
   ```
   *Nota: Asegúrate de que el servicio `agnux.service.ts` apunte a la IP de tu backend.*

---

## 🛠️ Cómo colaborar (¡Se busca ayuda!)

Actualmente, el proyecto está en una fase de rápida expansión y busco colegas apasionados por los agentes autónomos, la ingeniería de prompts y arquitecturas asíncronas para resolver los siguientes desafíos:

- **Optimización del Orquestador de Tools**: El extractor heurístico actual usa RegEx en `intent_orchestrator.py` para interceptar bloques de código en texto plano desde `/api/generate` de Ollama. Buscamos formas más nativas o resilientes de gestionar "Tool Calling".
- **Memoria Semántica**: Mejorar el threshold (umbral de corte) y la similitud del coseno usando algoritmos más finos sobre la colección `agnux_kernel_memory`.
- **UI en Angular**: Mejorar el motor de parsing de EventStreams (SSE) y la gestión del z-index de las ventanas flotantes en el `EscritorioComponent`.

**Si tienes ideas o encuentras bugs, no dudes en abrir un Issue o mandar un Pull Request.**

---

<div align="center">
  <sub>Construido para el futuro del procesamiento edge. 📡</sub>
</div>
