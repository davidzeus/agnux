# 🏠 Configuración de Ollama Local para AGNUX

Ollama es el runtime de IA que ejecuta modelos de lenguaje en tu máquina **sin depender de APIs en la nube**. Esta guía te explica cómo configurarlo correctamente.

## ¿Qué es Ollama?

**Ollama** es un servidor HTTP que ejecuta modelos de IA localmente. AGNUX se conecta a él para hacer consultas de forma completamente **offline** o como **fallback** si la nube no funciona.

## 📥 Instalación de Ollama

### En Linux (Ubuntu/Debian)

```bash
# Opción 1: Script de instalación automática (RECOMENDADO)
curl -fsSL https://ollama.ai/install.sh | sh

# Opción 2: Descarga manual desde
# https://ollama.ai/download
```

### En macOS
```bash
# Descargar desde: https://ollama.ai/download/mac
# O con Homebrew:
brew install ollama
```

### En Windows
Descarga desde: https://ollama.ai/download/windows

---

## 🚀 Iniciar Ollama

### Opción 1: Ejecutable Manual (Desarrollo)

```bash
# En una terminal dedicada, inicia Ollama
ollama serve

# Deberías ver:
# Listening on 127.0.0.1:11434 (http)
```

⚠️ **Importante**: Mantén esta terminal abierta. Si la cierras, Ollama se detiene.

### Opción 2: Servicio Automático (Producción)

En **Linux**, Ollama se instala como servicio `systemd`:

```bash
# Ver estado
sudo systemctl status ollama

# Iniciar servicio
sudo systemctl start ollama

# Habilitar en el arranque
sudo systemctl enable ollama

# Ver logs
sudo journalctl -u ollama -f
```

---

## 📦 Descargar Modelos

Antes de usar AGNUX con Ollama, necesitas descargar un modelo.

### Modelos Recomendados

| Modelo | Velocidad | Calidad | Uso |
|--------|-----------|---------|-----|
| `qwen2.5:1.5b` ⭐ | Muy rápido | Buena | Chat general, AGNUX default |
| `mistral` | Rápido | Excelente | Chat avanzado |
| `neural-chat` | Rápido | Buena | Optimizado para conversación |
| `llama2` | Medio | Excelente | Análisis y tareas complejas |
| `dolphin-mixtral` | Lento | Excelente | Reasoning avanzado |

### Descargar Modelos

```bash
# Descargar el modelo recomendado
ollama pull qwen2.5:1.5b

# Descargar otros modelos
ollama pull mistral
ollama pull neural-chat
ollama pull llama2

# Listar modelos descargados
ollama list

# Ejemplo de salida:
# NAME                DIGEST              SIZE    MODIFIED
# qwen2.5:1.5b       abc123...           952MB   2 minutes ago
# mistral             def456...           4.1GB   5 minutes ago
```

---

## 🔗 Conectar AGNUX a Ollama

### 1. Verificar que Ollama está corriendo

```bash
# Debería devolver una respuesta JSON
curl http://127.0.0.1:11434/api/tags

# Ejemplo de respuesta correcta:
# {"models":[{"name":"qwen2.5:1.5b","modified_at":"2025-05-27T14:32:10Z",...}]}
```

### 2. Configurar Variables de Entorno

En el directorio de AGNUX, crea o edita `.env`:

```bash
# .env
AGNUX_IA_PROVIDER=local
AGNUX_ACTIVE_MODEL=qwen2.5:1.5b
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### 3. Iniciar AGNUX

```bash
cd backend
export AGNUX_IA_PROVIDER=local
export AGNUX_ACTIVE_MODEL=qwen2.5:1.5b
python3 -m uvicorn app:app --reload --port 8000
```

### 4. Verificar Conexión

```bash
# En otra terminal
curl -X POST http://localhost:8000/api/system/intent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hola, ¿cómo estás?"}'

# Respuesta esperada:
# {"status": "success", "response": "Hola, estoy bien..."}
```

---

## ⚙️ Configuración Avanzada de Ollama

### Cambiar Puerto

Por defecto Ollama usa `http://127.0.0.1:11434`. Para cambiar:

```bash
# Establecer variable de entorno
export OLLAMA_HOST=127.0.0.1:9999

# Luego iniciar Ollama
ollama serve

# Actualizar AGNUX
export OLLAMA_BASE_URL=http://127.0.0.1:9999
```

### Cambiar Modelo en Tiempo Real

```bash
# Sin reiniciar AGNUX, solo cambia la variable
export AGNUX_ACTIVE_MODEL=mistral

# El siguiente request usará mistral
```

### Usar Múltiples Modelos

En `backend/app.py` puedes agregar lógica para elegir modelos según el contexto:

```python
# Ejemplo: usar modelos diferentes según la tarea
if "análisis" in payload.prompt.lower():
    modelo = "dolphin-mixtral"
elif "rápido" in payload.prompt.lower():
    modelo = "qwen2.5:1.5b"
else:
    modelo = "mistral"
```

### Optimizar Rendimiento

```bash
# Aumentar contexto (puede usar más RAM)
export OLLAMA_NUM_THREADS=8

# Usar GPU si disponible
export OLLAMA_CUDA_VISIBLE_DEVICES=0

# Ver opciones
ollama serve --help
```

---

## 🆘 Troubleshooting

### ❌ Error: "Connection refused: http://127.0.0.1:11434"

**Solución**: Ollama no está corriendo.

```bash
# En una terminal diferente
ollama serve
```

### ❌ Error: "Model 'qwen2.5:1.5b' not found"

**Solución**: Descarga el modelo primero.

```bash
ollama pull qwen2.5:1.5b
```

### ❌ Error: "timeout after 45s"

**Solución**: El modelo está tardando mucho. Prueba con uno más pequeño:

```bash
export AGNUX_ACTIVE_MODEL=qwen2.5:1.5b  # más pequeño
```

### ❌ Ollama ocupa mucha RAM/CPU

**Solución**: Usa un modelo más pequeño o reduce parámetros:

```bash
export OLLAMA_NUM_THREADS=4  # Menos threads
export OLLAMA_NUM_GPU=0       # Forzar CPU
```

### ❌ Quiero descargar modelos en la nube

**Nota**: Ollama descarga modelos **localmente**. Esto requiere espacio en disco:

- `qwen2.5:1.5b`: ~1GB
- `mistral`: ~4GB
- `neural-chat`: ~4GB
- `llama2`: ~4GB

Asegúrate de tener suficiente espacio:

```bash
df -h  # Ver espacio disponible
```

---

## 📊 Monitoreo de Ollama

### Ver Modelos Cargados

```bash
ollama list
```

### Ver Memoria Usada

```bash
# Linux
ps aux | grep ollama

# Ver uso de GPU (si aplica)
nvidia-smi  # Para NVIDIA GPUs
```

### Ver Logs

```bash
# Linux (systemd)
sudo journalctl -u ollama -f

# macOS
log stream --predicate 'process == "ollama"'
```

---

## 🔄 Failover Automático (Híbrido Nube + Local)

Si configuras AGNUX con Gemini o OpenAI:

```bash
export AGNUX_IA_PROVIDER=gemini  # Usar nube
export AGNUX_ACTIVE_MODEL=gemini-2.5-flash
export GEMINI_API_KEY=AIzaSy...
```

**AGNUX automáticamente replica a Ollama si**:
- La API de Gemini falla (error HTTP, timeout)
- No hay conexión a internet
- La API devuelve un error 429 (rate limit)

Esto significa que **siempre tienes una opción offline** incluso usando proveedores de nube.

---

## 📚 Enlaces Útiles

- **Ollama Official**: https://ollama.ai
- **Ollama GitHub**: https://github.com/ollama/ollama
- **Modelos Disponibles**: https://ollama.ai/library
- **Documentación Técnica**: https://github.com/ollama/ollama/wiki

---

## 🎯 Resumen Rápido

```bash
# 1. Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Descargar modelo
ollama pull qwen2.5:1.5b

# 3. Iniciar Ollama (en terminal dedicada)
ollama serve

# 4. Configurar AGNUX
export AGNUX_IA_PROVIDER=local
export AGNUX_ACTIVE_MODEL=qwen2.5:1.5b

# 5. Iniciar AGNUX
cd backend
python3 -m uvicorn app:app --reload

# ✅ ¡Listo!
```

---

**Versión**: 1.0 | **Última actualización**: Mayo 2025
