# 🚀 AGNUX — Guía de Inicio Rápido

## 🎯 En 5 minutos

### 1. Instalar Ollama (IA Local)

```bash
# Descargar e instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Iniciar Ollama en una terminal (se mantiene corriendo)
ollama serve

# En otra terminal, descargar un modelo
ollama pull qwen2.5:1.5b
```

✅ Ollama estará disponible en `http://127.0.0.1:11434`

### 2. Configurar el Backend (Python)

```bash
cd /home/david/Documentos/agnux

# Crear entorno virtual
python3 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Iniciar el Backend

```bash
cd backend

# Con Ollama local (RECOMENDADO)
export AGNUX_IA_PROVIDER=local
export AGNUX_ACTIVE_MODEL=qwen2.5:1.5b

# Ejecutar servidor
python3 -m uvicorn app:app --reload --port 8000
```

Deberías ver:
```
✅ Uvicorn running on http://127.0.0.1:8000
✅ 🚀 NÚCLEO CONFIGURADO -> Runtime: local
```

### 4. Probar la API (en otra terminal)

```bash
curl -X POST http://localhost:8000/api/system/intent \
  -H "Content-Type: application/json" \
  -d '{"prompt": "¿Cuál es el estado de mi hardware?"}'
```

Respuesta esperada:
```json
{
  "status": "success",
  "response": "{\"cpu_percent\": 45.2, \"memory_percent\": 62.1, ...}"
}
```

### 5. Iniciar el Frontend (Angular) - OPCIONAL

```bash
cd frontend
npm install
npm start
```

Accede a: **http://localhost:4200**

---

## ⚙️ Configuración Avanzada

### Usar Gemini (con fallback a Ollama)

```bash
export AGNUX_IA_PROVIDER=gemini
export AGNUX_ACTIVE_MODEL=gemini-2.5-flash
export GEMINI_API_KEY=AIzaSy...

cd backend
python3 -m uvicorn app:app --reload --port 8000
```

**Si Gemini falla**, AGNUX automáticamente usa Ollama local. ✅

### Usar otros modelos de Ollama

```bash
# Listar modelos disponibles
ollama list

# Descargar más modelos
ollama pull mistral
ollama pull neural-chat

# Usar otro modelo
export AGNUX_ACTIVE_MODEL=mistral
```

---

## ✅ Checklist de Verificación

- [ ] Ollama está corriendo: `curl http://127.0.0.1:11434/api/tags`
- [ ] Modelo descargado: `ollama list | grep qwen`
- [ ] Variables de entorno: `echo $AGNUX_IA_PROVIDER`
- [ ] Backend inicia sin errores
- [ ] API responde: `curl http://localhost:8000/api/system/intent ...`

---

## 🆘 Problemas Comunes

| Error | Solución |
|---|---|
| `Connection refused http://127.0.0.1:11434` | Ollama no está corriendo. Ejecuta `ollama serve` |
| `Model not found: qwen2.5:1.5b` | Descarga: `ollama pull qwen2.5:1.5b` |
| `No module named 'agno'` | Instala: `pip install -r requirements.txt` |
| `Port 8000 already in use` | Cambia puerto: `--port 9000` |

---

## 📚 Documentación Completa

Ver [README.md](README.md) para detalles técnicos completos.

## 💡 Próximos Pasos

- Explorar `backend/app.py` para entender el flujo
- Crear herramientas dinámicas (el agente las crea automáticamente)
- Integrar con el frontend Angular
- Desplegar como servicio systemd

¡Listo! 🎉
