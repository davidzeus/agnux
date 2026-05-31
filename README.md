<div align="center">

  <img src="https://agnux.net.ar/src/index.png" alt="AGNUX OS" width="480" />

  <h1>🧠 AGNUX OS</h1>

  <p><strong>Un Sistema Operativo Cognitivo, Autónomo y Autogenerador<br/>impulsado por IA local, Metaprogramación y Zero-Trust Security</strong></p>

  <p>
    <a href="https://fastapi.tiangolo.com/">
      <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI"/>
    </a>
    <a href="https://angular.io/">
      <img src="https://img.shields.io/badge/Angular-DD0031?style=for-the-badge&logo=angular&logoColor=white" alt="Angular"/>
    </a>
    <a href="https://ollama.ai/">
      <img src="https://img.shields.io/badge/Ollama-000000?style=for-the-badge&logo=Ollama&logoColor=white" alt="Ollama"/>
    </a>
    <a href="https://qdrant.tech/">
      <img src="https://img.shields.io/badge/Qdrant-FF5252?style=for-the-badge&logo=qdrant&logoColor=white" alt="Qdrant"/>
    </a>
    <a href="https://www.cloudflare.com/">
      <img src="https://img.shields.io/badge/Cloudflare_Access-F38020?style=for-the-badge&logo=cloudflare&logoColor=white" alt="Cloudflare"/>
    </a>
    <a href="https://www.docker.com/">
      <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>
    </a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/Estado-En_Desarrollo_Activo-00ff66?style=flat-square" alt="Estado"/>
    <img src="https://img.shields.io/badge/IA-100%25_Local_%26_Privada-blueviolet?style=flat-square" alt="IA Local"/>
    <img src="https://img.shields.io/badge/LLM-Llama3.1_%2B_Qwen2.5-orange?style=flat-square" alt="LLM"/>
    <img src="https://img.shields.io/badge/Se_buscan-Colaboradores-ff3366?style=flat-square" alt="Colaboradores"/>
  </p>

  <br/>

  <blockquote>
    <em>"No construí otro chatbot. Construí el kernel de un sistema operativo donde la IA es el proceso raíz."</em>
    <br/>
    — <strong>David González</strong> · 🇦🇷 Desde Argentina para el mundo
  </blockquote>

</div>

---

## 🤔 ¿Qué es AGNUX OS?

**AGNUX OS** no es simplemente un asistente virtual. Es una arquitectura de **Kernel Cognitivo** diseñada para gobernar hardware, interfaces de usuario y bases de datos mediante el razonamiento semántico de grandes modelos de lenguaje (LLMs) corriendo **100% en tu propio hardware, con 100% de privacidad**.

AGNUX corre en servidores de alto rendimiento (como un *Lenovo SR630*) y actúa como el **cerebro maestro** de múltiples terminales conectadas a través de la red. Desde su escritorio flotante en el navegador, cualquier usuario autenticado puede hablarle a la IA como si tuviese un ingeniero de sistemas a su disposición: que ejecute comandos en el host, que controle servicios, que se programe a sí misma nuevas habilidades... todo sin escribir una sola línea de código.

---

## ✨ Características Principales

### 🧬 Autogénesis — Metaprogramación en Caliente

> AGNUX puede **escribir su propio código** en tiempo real.

Cuando el Agente detecta una intención del usuario que no puede resolver con sus herramientas estáticas, genera un script Python, lo guarda en el host bajo `dynamic_tools/`, lo compila en memoria y lo ejecuta instantáneamente **sin reiniciar el servidor**. Si la tool que necesitas no existe, la IA simplemente te pregunta: *"¿Quieres que la programe?"* y si dices que sí, ¡la escribe y la ejecuta en segundos!

### 🛡️ Zero-Trust Security con Cloudflare Access

El acceso al escritorio está protegido por una cadena de seguridad doble:
- **Cloudflare Access (Zero-Trust):** El túnel público no expone el servidor directamente. Cloudflare actúa como guardián de identidad, autenticando al usuario con su cuenta de Google mediante OAuth2 antes de siquiera tocar el backend.
- **Validación en Backend:** Una vez que Cloudflare autentica al usuario, el Backend de FastAPI verifica el JWT de Cloudflare, extrae el email del usuario y lo mapea a su perfil de AGNUX. Si el token no es válido, el socket se corta.
- **Resultado:** No hay login customizado vulnerable. No hay contraseñas expuestas. Google y Cloudflare garantizan que solo *tú* puedes entrar.

### 🧠 Memoria Episódica y Router Semántico (Omnisciencia)

- **Qdrant Vector DB:** Toda interacción, ejecución de herramienta o evento del sistema se vectoriza (`SentenceTransformer: paraphrase-multilingual-mpnet-base-v2`, 768 dimensiones) y se persiste en colecciones separadas.
- **Recuperación de Contexto Automática:** Antes de cada inferencia, AGNUX inyecta silenciosamente los recuerdos más relevantes del usuario en el prompt del sistema, creando una ilusión real de omnisciencia y continuidad conversacional.
- **Umbral Semántico Dinámico:** El Router calcula la similitud de coseno entre el prompt del usuario y los *embeddings* de cada herramienta disponible, enviando a la IA solo las tools más relevantes para ahorrar contexto y mejorar la precisión.

### ⚡ Escritorio Reactivo (Event-Driven UI)

El Backend y el Frontend se comunican exclusivamente mediante flujos **SSE (Server-Sent Events)** y **WebSockets**. El escritorio es un canvas vivo que reacciona a eventos del Kernel en tiempo real:

| Evento del Kernel | Resultado en el Escritorio |
|---|---|
| `CREATE_WINDOW` | Abre una ventana flotante con HTML dinámico |
| `TOKEN` | Muestra la respuesta de la IA token a token (efecto máquina de escribir) |
| `SET_WALLPAPER` | Cambia el fondo del escritorio al instante |
| `SET_THEME` | Inyecta un bloque de CSS global, rediseñando toda la interfaz en tiempo real |
| `OPEN_MEDIA` | Abre una pestaña externa con música, video, etc. |
| `TOOL_RESULT` | Muestra el resultado de una herramienta ejecutada en el host |

### 🎨 Temas CSS en Tiempo Real (Runtime Theming)

La IA puede rediseñar toda la interfaz de AGNUX **simplemente hablando**. El sistema de variables CSS globales (`--agnux-accent`, `--agnux-panel-bg`, `--agnux-bg-color`, etc.) permite que la IA genere un bloque de CSS que el Frontend inyecta directamente en el `<head>` del DOM, recalculando todos los colores, fuentes y gradientes sin recargar la página.

---

## 🏗️ Arquitectura del Sistema

```text
agnux/
├── backend/                         # Kernel del sistema (FastAPI + Python)
│   ├── main.py                      # Entrypoint, CORS y middlewares
│   ├── core/
│   │   ├── config.py                # Variables de entorno (.env)
│   │   └── memory.py                # Instancia de Qdrant y caché vectorial en RAM
│   ├── schemas/
│   │   └── models.py                # Modelos Pydantic (validación estricta)
│   ├── services/
│   │   ├── intent_orchestrator.py   # 🧠 Motor de Inferencia Asíncrona (El Cerebro)
│   │   └── tools_service.py         # Catálogo de herramientas del sistema
│   ├── api/
│   │   └── routes/
│   │       ├── intent.py            # SSE, WebSockets e inferencia de flujos
│   │       └── auth.py              # Autenticación Cloudflare JWT + Google OAuth2
│   ├── dynamic_tools/               # 🧬 Scripts auto-generados por la IA en caliente
│   └── tools/                       # Herramientas estáticas del host
│
├── frontend/                        # Escritorio de Usuario (Angular)
│   └── src/app/
│       ├── components/
│       │   ├── escritorio/          # Desktop principal, clock, barra de comandos
│       │   ├── ventana/             # Ventanas flotantes drag & drop, redimensionables
│       │   └── hyper-island/        # Panel de sistema e información de red
│       └── services/
│           ├── agnux.service.ts     # Bus de streaming SSE (cliente del Kernel)
│           ├── auth.service.ts      # Validación Cloudflare JWT en el cliente
│           └── theme.service.ts     # Motor de inyección CSS en tiempo real
│
├── bare-metal/                      # 💿 Entorno de distribución (AGNUX OS ISO)
│   ├── build-iso.sh                 # Compilador maestro de la ISO
│   ├── Makefile                     # Automatización de tareas
│   ├── boot/                        # Customización de GRUB y splash screen
│   ├── config/                      # Configuraciones de inicio (Kiosk Openbox, Systemd)
│   └── scripts/                     # Scripts bash de aprovisionamiento de hardware
│
└── docker-compose.yml               # Orquestación de contenedores
```

---

## 💿 Distribución Bare-Metal (AGNUX OS ISO)

El directorio `bare-metal/` contiene las herramientas para compilar AGNUX OS en una imagen ISO booteable, lista para ser instalada directamente en el hardware final.

### 🐧 ¿Por qué usamos Ubuntu Server como base?

Aprovechamos la imagen de Ubuntu Server fundamentalmente por su inmenso soporte de drivers pre-configurados (especialmente redes y adaptadores) y su robustez empresarial. Usamos Ubuntu **sólo como base Live CD**. En el proceso de construcción, el script extrae la estructura del sistema, le inyecta nuestro Kernel (backend y frontend) junto con las personalizaciones del arranque, reemplazando el comportamiento estándar. Esto nos evita programar un sistema Linux desde cero, permitiendo enfocarnos en la capa cognitiva y visual del OS.

### 📂 ¿Qué hacen los scripts `.sh`?

- **`build-iso.sh`**: Es el orquestador principal. Descarga la ISO de Ubuntu de forma automática, desempaqueta su sistema de archivos en el espacio de usuario (sin requerir montajes complejos con loop que suelen causar problemas), inyecta los componentes de AGNUX y las configuraciones de la carpeta `bare-metal/config/`, y vuelve a comprimir todo (SquashFS) sellando una ISO nueva y lista para flashear en un pendrive.
- **`scripts/setup-agnux.sh`**: Es un script de post-instalación inyectado dentro del sistema operativo. Se asegura de instalar dependencias clave (Xorg, Docker, entorno de ventana minimalista) y deja preparado el escenario para que AGNUX inicie a pantalla completa.
- **`scripts/install-drivers.sh`**: Evalúa el hardware en el que se ejecuta el sistema. Si detecta tarjetas gráficas NVIDIA, instala dinámicamente los controladores privativos y el toolkit de CUDA, garantizando que el entorno local de Ollama e inferencia de los LLMs tenga acceso completo a la aceleración por GPU sin intervención del usuario.

---

## 🚀 Configuración y Despliegue

> [!NOTE]
> **Estado de Despliegue**: El ecosistema está completamente dockerizado para facilitar el despliegue. El objetivo arquitectónico final es montarlo de forma nativa en **bare-metal Kernel Linux** para maximizar el control de hardware y la ejecución de subprocesos de bajo nivel.

### Hardware Recomendado

Dado que AGNUX opera con modelos LLM locales en caliente y modelos de embeddings en RAM, se recomienda hardware robusto para una experiencia fluida:

| Componente | Mínimo | Referencia de Desarrollo |
|---|---|---|
| **GPU** | NVIDIA 8GB VRAM | RTX 5070 (12GB VRAM) |
| **CPU** | 8 núcleos | Intel i7-12700F |
| **RAM** | 32GB DDR4 | 64GB DDR4 |
| **Almacenamiento** | 50GB SSD | NVMe dedicado |

### Prerrequisitos de Software

- **Docker** y **Docker Compose**
- **Node.js 18+** y **Angular CLI 15+**
- Nodos de **Ollama** con los modelos `llama3.1:8b` (razonamiento) y `qwen2.5-coder:7b` (herramientas)
- Nodo de **Qdrant DB** expuesto en el puerto `6333`
- Una cuenta en **Cloudflare** con un túnel configurado apuntando a tu servidor

### Instalación Rápida con Docker

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/agnux.git
cd agnux

# 2. Configurar variables de entorno
cp backend/.env.example backend/.env
# Editar backend/.env con los datos de tu nodo Ollama, Qdrant y Cloudflare

# 3. Levantar todo el ecosistema
docker-compose up -d --build

# 4. Abrir en el navegador (a través de tu túnel de Cloudflare)
# https://tu-dominio.com
```

### Variables de Entorno (`backend/.env`)

```env
# Motor de IA (Ollama)
OLLAMA_HOST=http://<IP_NODO_OLLAMA>:11434
AGNUX_ACTIVE_MODEL=llama3.1:8b
AGNUX_CODER_MODEL=qwen2.5-coder:7b

# Base de datos vectorial (Qdrant)
QDRANT_HOST=http://<IP_NODO_QDRANT>:6333

# Seguridad (Cloudflare Access)
CLOUDFLARE_TEAM_DOMAIN=<tu-equipo>.cloudflareaccess.com

# Integraciones externas
GOOGLE_CLIENT_ID=<tu-client-id>
GOOGLE_CLIENT_SECRET=<tu-client-secret>
```

---

## 🛠️ ¿Cómo Colaborar? ¡Se busca equipo!

Este proyecto está en **expansión activa** y busco colegas apasionados por los agentes autónomos, la ingeniería de prompts y las arquitecturas asíncronas. Estas son las áreas donde la ayuda tiene mayor impacto:

### 🔥 Desafíos Abiertos

- **🧩 Tool Calling Nativo:** El extractor heurístico actual usa RegEx sobre el stream de Ollama para interceptar llamadas a herramientas. Queremos migrar a la API de `tool_calling` nativo de Ollama para mayor robustez.
- **🧠 Memoria Semántica Avanzada:** Mejorar el umbral de similitud de coseno en la colección `agnux_kernel_memory` y explorar estrategias de re-ranking.
- **🎨 Motor de Temas CSS:** Expandir el sistema de temas para incluir perfiles pre-guardados y transiciones animadas entre temas.
- **📱 Interfaz Responsive:** El escritorio está optimizado para pantallas grandes. Necesitamos una versión tablet/móvil del escritorio.
- **🔐 OAuth2 con Google Workspace:** Integración completa para que la IA pueda redactar correos en Gmail, crear documentos en Drive y agendar reuniones en Calendar de forma nativa desde el backend.
- **🐛 Testing E2E:** No tenemos tests de integración. ¡Cualquier contribución con Playwright o Cypress es bienvenida!

### 📋 ¿Cómo contribuir?

1. Haz un **Fork** del repositorio.
2. Crea una rama descriptiva: `git checkout -b feature/nombre-de-la-feature`.
3. Commitea tus cambios con mensajes claros.
4. Abre un **Pull Request** describiendo qué cambiaste y por qué.

**Si encontrás un bug o tenés una idea, no dudes en abrir un [Issue](../../issues).** Toda participación es bienvenida, desde documentación hasta arquitectura de kernel.

---

## ☕ Apoya el Proyecto

Si este proyecto te resulta útil o te inspira, podés apoyar su desarrollo invitándome un café simbólico a través de **Mercado Pago** (Argentina).  
Toda contribución es enorme para mantener los servidores locales, GPUs y horas de desarrollo activo.

- **Alias Mercado Pago:** `gonzalez360.mp`

¡Mil gracias por el apoyo!

---

## 📄 Licencia

Distribuido bajo la licencia **MIT**. Ve el archivo `LICENSE` para más información.

---

<div align="center">

  <h3>🇦🇷 Hecho con pasión en Argentina</h3>

  <p>
    Un saludo desde el sur del mundo. Este proyecto nació de la idea de que la inteligencia artificial no debería vivir en la nube de nadie más que en la tuya.<br/>
    Si llegaste hasta acá, ya somos equipo.
  </p>

  <p><strong>— David González</strong> · <em>Desde Argentina para el mundo 🌍</em></p>

  <br/>

  <sub>Construido para el futuro del procesamiento edge y la soberanía tecnológica. 📡</sub>

</div>
