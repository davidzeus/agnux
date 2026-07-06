// =====================================================================
// 🚀 AGNUX OS v2.0 - Client Shell Controller
// =====================================================================

const API_BASE = "http://127.0.0.1:8000";

document.addEventListener("DOMContentLoaded", () => {
    inicializarReloj();
    inicializarArrastreVentanas();
    inicializarSpotlight();
    comenzarMonitoreoTelemetry();
    inicializarInputsVentanas();
    conectarWebSocketNotificaciones("terminal-default", "user-default");
});

// WebSocket Client for Hyperisland Notifications
let notificationSocket = null;
function conectarWebSocketNotificaciones(terminalId = "terminal-default", userId = "user-default") {
    const wsUrl = `ws://127.0.0.1:8000/api/system/notifications/ws/${terminalId}/${userId}`;
    console.log(`🔌 [WEBSOCKET] Conectando a canal de notificaciones: ${wsUrl}`);
    
    notificationSocket = new WebSocket(wsUrl);
    
    notificationSocket.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload.type === "notification") {
                const msg = payload.data.message;
                // Show notification in hyperisland
                setHyperisland(msg, "capsule-expanded");
            }
        } catch (e) {
            console.error("Error parsing WS message:", e);
        }
    };
    
    notificationSocket.onclose = () => {
        console.warn("🔌 [WEBSOCKET] Conexión cerrada. Reintentando en 5 segundos...");
        setTimeout(() => conectarWebSocketNotificaciones(terminalId, userId), 5000);
    };
    
    notificationSocket.onerror = (err) => {
        console.error("🔌 [WEBSOCKET] Error detectado:", err);
    };
}

// Dedicated Window chat input initiator (static win-console)
function inicializarInputsVentanas() {
    const consoleWin = document.getElementById("win-console");
    if (consoleWin) {
        const input = consoleWin.querySelector(".window-input");
        const btn = consoleWin.querySelector(".window-send-btn");
        const enviarMsg = () => {
            const text = input.value.trim();
            if (text) {
                enviarPromptAlKernel(text, "win-console");
                input.value = "";
            }
        };
        if (btn && input) {
            btn.addEventListener("click", enviarMsg);
            input.addEventListener("keydown", (e) => {
                if (e.key === "Enter") enviarMsg();
            });
        }
    }
}

// 1. Clock Manager
function inicializarReloj() {
    const clockEl = document.getElementById("system-time");
    const actualizar = () => {
        const ahora = new Date();
        let horas = ahora.getHours();
        let minutos = ahora.getMinutes();
        const ampm = horas >= 12 ? 'PM' : 'AM';
        horas = horas % 12;
        horas = horas ? horas : 12;
        minutos = minutos < 10 ? '0' + minutos : minutos;
        clockEl.textContent = `${horas}:${minutos} ${ampm}`;
    };
    actualizar();
    setInterval(actualizar, 1000);
}

// 2. Hyperisland (Dynamic Island) Status Controller
let islandTimeout = null;
function setHyperisland(text, stateClass = "capsule-compact") {
    const island = document.getElementById("hyperisland");
    const label = document.getElementById("hyperisland-text");
    
    label.textContent = text;
    island.className = stateClass;
    
    // Auto collapse after 5 seconds if expanded
    if (stateClass === "capsule-expanded") {
        if (islandTimeout) clearTimeout(islandTimeout);
        islandTimeout = setTimeout(() => {
            island.className = "capsule-compact";
            label.textContent = "Agnux Kernel listo";
        }, 5000);
    }
}

// 3. Draggable Windows System
let activeWindow = null;
let dragOffset = { x: 0, y: 0 };

function inicializarArrastreVentanas() {
    const headers = document.querySelectorAll(".window-header, .widget-header");
    headers.forEach(header => {
        header.addEventListener("mousedown", (e) => {
            activeWindow = header.parentElement;
            
            // Layering management: keep widgets behind standard windows
            if (activeWindow.classList.contains("desktop-widget")) {
                document.querySelectorAll(".desktop-widget").forEach(w => w.style.zIndex = 5);
                activeWindow.style.zIndex = 8;
            } else {
                document.querySelectorAll(".agnux-window").forEach(w => {
                    w.style.zIndex = 20;
                    w.classList.remove("win-focused");
                });
                activeWindow.style.zIndex = 50;
                activeWindow.classList.add("win-focused");
            }
            
            const rect = activeWindow.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            
            document.addEventListener("mousemove", moverVentana);
            document.addEventListener("mouseup", detenerArrastre);
        });
    });
}

function moverVentana(e) {
    if (!activeWindow) return;
    const desktop = document.getElementById("agnux-desktop");
    const deskRect = desktop.getBoundingClientRect();
    
    let left = e.clientX - dragOffset.x;
    let top = e.clientY - dragOffset.y;
    
    // Contain within desktop bounds
    left = Math.max(0, Math.min(left, window.innerWidth - activeWindow.offsetWidth));
    top = Math.max(44, Math.min(top, window.innerHeight - activeWindow.offsetHeight - 80));
    
    activeWindow.style.left = `${left}px`;
    activeWindow.style.top = `${top}px`;
}

function detenerArrastre() {
    activeWindow = null;
    document.removeEventListener("mousemove", moverVentana);
    document.removeEventListener("mouseup", detenerArrastre);
}

// Window actions
function closeWindow(id) {
    const win = document.getElementById(id);
    if (win) {
        win.style.transform = "scale(0.92)";
        win.style.opacity = "0";
        setTimeout(() => {
            win.classList.add("hidden");
            win.style.transform = "";
            win.style.opacity = "";
        }, 200);
    }
}

function minimizeWindow(id) {
    const win = document.getElementById(id);
    if (win) {
        win.style.transform = "scale(0.8) translateY(100px)";
        win.style.opacity = "0";
        setTimeout(() => win.classList.add("hidden"), 200);
    }
}

function openWindow(id) {
    const win = document.getElementById(id);
    if (win) {
        if (win.classList.contains("hidden")) {
            win.classList.remove("hidden");
            win.style.transform = "scale(1)";
            win.style.opacity = "1";
            // Re-disparar la animación de aparición (window-spawn)
            win.style.animation = "none";
            void win.offsetWidth;
            win.style.animation = "";
            if (win.classList.contains("desktop-widget")) {
                win.style.zIndex = 5;
            } else {
                win.style.zIndex = 50;
            }
        } else {
            // Toggles close/hide when clicked on dock again
            closeWindow(id);
        }
    }
}

function maximizeWindow(id) {
    const win = document.getElementById(id);
    if (win) {
        if (win.style.width === "100vw") {
            win.style.width = "560px";
            win.style.height = "420px";
            win.style.top = "100px";
            win.style.left = "100px";
        } else {
            win.style.width = "100vw";
            win.style.height = "calc(100vh - 140px)";
            win.style.top = "44px";
            win.style.left = "0px";
        }
    }
}

// 4. Spotlight & Query Dispatcher
function inicializarSpotlight() {
    const input = document.getElementById("spotlight-input");
    const btn = document.getElementById("spotlight-send-btn");
    
    const enviar = () => {
        const val = input.value.trim();
        if (val) {
            enviarPromptAlKernel(val);
            input.value = "";
        }
    };
    
    btn.addEventListener("click", enviar);
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") enviar();
    });
}

// Spawns app requests to host via API
function runApp(appId) {
    enviarPromptAlKernel(`abrir ${appId}`);
}

// 5. Streams the user intent and parses the response
// 5. Streams the user intent and parses the response
async function enviarPromptAlKernel(promptText, windowId = "win-console") {
    // Show console window if it is hidden, so user sees the streaming text
    if (windowId === "win-console") {
        const consoleWin = document.getElementById("win-console");
        if (consoleWin && consoleWin.classList.contains("hidden")) {
            consoleWin.classList.remove("hidden");
            consoleWin.style.transform = "scale(1)";
            consoleWin.style.opacity = "1";
            consoleWin.style.zIndex = 50;
        }
    }
    
    appendMessage("user", promptText, windowId);
    
    const indicator = obtenerIndicadorStream(windowId);
    if (indicator) indicator.classList.remove("hidden");
    
    setHyperisland("Enrutando intenciones...", "capsule-expanded");
    
    try {
        const response = await fetch(`${API_BASE}/api/system/intent`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                prompt: promptText,
                user_id: "user-default",
                terminal_id: windowId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let currentEvent = null;
        let lastMessageEl = null;
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            let lines = buffer.split("\n");
            buffer = lines.pop(); // Keep last incomplete chunk in buffer
            
            for (let line of lines) {
                line = line.trim();
                if (!line) continue;
                
                if (line.startsWith("event:")) {
                    currentEvent = line.substring(6).trim();
                } else if (line.startsWith("data:")) {
                    const dataVal = line.substring(5).trim();
                    handleEvent(currentEvent, dataVal, (el) => { lastMessageEl = el; }, windowId);
                    currentEvent = null;
                } else {
                    // Try direct JSON
                    try {
                        const parsed = JSON.parse(line);
                        handleDirectJson(parsed, (el) => { lastMessageEl = el; }, windowId);
                    } catch (e) {
                        // Plain text chunk fallback
                        appendStreamChunk(line, (el) => { lastMessageEl = el; }, windowId);
                    }
                }
            }
        }
    } catch (err) {
        appendMessage("system", `Error de red en el Kernel: ${err.message}`, windowId);
        setHyperisland("Fallo de comunicación", "capsule-compact");
    } finally {
        if (indicator) indicator.classList.add("hidden");
    }
}

// Helper to retrieve correct log container
function obtenerLogContenedor(windowId) {
    if (!windowId || windowId === "win-console") {
        return document.getElementById("console-log");
    }
    const win = document.getElementById(windowId);
    return win ? win.querySelector(".window-chat-log, .console-content") || win.querySelector(".window-content") : null;
}

function obtenerIndicadorStream(windowId) {
    if (!windowId || windowId === "win-console") {
        return document.getElementById("console-stream-indicator");
    }
    const win = document.getElementById(windowId);
    return win ? win.querySelector(".stream-indicator") : null;
}

// Append text to chat console
function appendMessage(sender, text, windowId = "win-console") {
    let log = obtenerLogContenedor(windowId);
    if (!log) return null;
    
    // Fallback if class mismatch
    if (log.classList.contains("window-content") && log.querySelector(".window-chat-log")) {
        log = log.querySelector(".window-chat-log");
    }
    
    const msg = document.createElement("div");
    msg.className = `message ${sender}-msg`;
    msg.innerHTML = `<span class="sender">${sender === 'user' ? 'TÚ' : 'AGNUX'}:</span><p>${text}</p>`;
    log.appendChild(msg);
    log.scrollTop = log.scrollHeight;
    return msg;
}

function appendStreamChunk(text, setLastElCallback, windowId = "win-console") {
    let log = obtenerLogContenedor(windowId);
    if (!log) return;
    
    // Fallback if class mismatch
    if (log.classList.contains("window-content") && log.querySelector(".window-chat-log")) {
        log = log.querySelector(".window-chat-log");
    }
    
    // Find the last kernel-msg or create one
    let lastMsg = log.lastElementChild;
    if (!lastMsg || !lastMsg.classList.contains("kernel-msg")) {
        lastMsg = document.createElement("div");
        lastMsg.className = "message kernel-msg";
        lastMsg.innerHTML = `<span class="sender">AGNUX:</span><p></p>`;
        log.appendChild(lastMsg);
    }
    
    const p = lastMsg.querySelector("p");
    p.textContent += text;
    log.scrollTop = log.scrollHeight;
    
    if (setLastElCallback) setLastElCallback(lastMsg);
}

// 6. Handle event schemas (SSE or direct JSON lines)
function handleEvent(event, dataStr, setLastElCallback, windowId = "win-console") {
    let data = {};
    try {
        data = JSON.parse(dataStr);
    } catch (e) {
        data = { raw: dataStr };
    }
    
    if (event === "SET-THEME" || data.event === "SET-THEME") {
        const cssCode = data["css-code"] || data.cssCode || data.raw;
        if (cssCode) {
            aplicarCSSDinamico(cssCode);
            appendMessage("system", "🎨 Tema visual aplicado en caliente por el Motor de Estilos.", windowId);
            setHyperisland("Estilo actualizado", "capsule-expanded");
        }
    } else if (event === "SHOW-NOTIFICATION" || data.__agnux_event === "SHOW-NOTIFICATION") {
        const msg = data.message || data.mensaje || data.raw;
        setHyperisland(msg, "capsule-expanded");
    } else if (event === "CREATE-WINDOW" || data.event === "CREATE-WINDOW") {
        crearVentanaDinamica(data);
    } else if (event === "OPEN-SYSTEM-APP" || data.__agnux_event === "OPEN-SYSTEM-APP") {
        appendMessage("system", `Lanzando aplicación local: ${data["app-id"] || data.appId || "Desconocida"}`, windowId);
    } else if (event === "SET-WALLPAPER" || data.__agnux_event === "SET-WALLPAPER") {
        const imgUrl = data["image-url"] || data.imageUrl;
        if (imgUrl) {
            document.getElementById("agnux-wallpaper").style.backgroundImage = `url('${imgUrl}')`;
            appendMessage("system", "🖼️ Fondo de pantalla modificado por el Kernel.", windowId);
        }
    } else if (event === "TEXT-CHUNK") {
        const chunk = data.content || data.raw;
        if (chunk) {
            appendStreamChunk(chunk, setLastElCallback, windowId);
        }
    } else if (event === "ACTIVATE-SKILL" || data.event === "ACTIVATE-SKILL") {
        const skill = data.skill || data.raw;
        if (skill) {
            const statusEl = document.getElementById("superpowers-status");
            const labelEl = document.getElementById("superpowers-skill-name");
            statusEl.classList.remove("inactive");
            labelEl.textContent = `⚡ SP: ${skill.toUpperCase()}`;
            setHyperisland(`Habilidad activa: ${skill}`, "capsule-expanded");
            appendMessage("system", `⚡ Habilidad de Superpowers activada: ${skill}`, windowId);
        }
    }
}

function handleDirectJson(parsed, setLastElCallback, windowId = "win-console") {
    if (parsed.event === "ROUTER-START") {
        setHyperisland("Kernel: Analizando intenciones...", "capsule-compact");
    } else if (parsed.event === "TOOL-EXECUTE") {
        setHyperisland(`Ejecutando: ${parsed["tool-name"] || parsed.tool}`, "capsule-compact");
    } else if (parsed.event === "TEXT-CHUNK") {
        appendStreamChunk(parsed.content || "", setLastElCallback, windowId);
    } else if (parsed.event === "TOOL-RESULT") {
        // Log tool response inside console safely
        appendMessage("system", `Resultado de la herramienta: ${parsed.data}`, windowId);
    } else if (parsed.event === "QUEUE-WAIT") {
        appendMessage("system", `⚠️ Cola del Kernel ocupada: ${parsed.message}`, windowId);
    } else if (parsed.event === "ERROR") {
        appendMessage("system", `❌ Falla del Kernel: ${parsed.message}`, windowId);
    } else if (parsed.event === "ACTIVATE-SKILL") {
        const skill = parsed.skill;
        if (skill) {
            const statusEl = document.getElementById("superpowers-status");
            const labelEl = document.getElementById("superpowers-skill-name");
            statusEl.classList.remove("inactive");
            labelEl.textContent = `⚡ SP: ${skill.toUpperCase()}`;
            setHyperisland(`Habilidad activa: ${skill}`, "capsule-expanded");
            appendMessage("system", `⚡ Habilidad de Superpowers activada: ${skill}`, windowId);
        }
    }
}

// Injects Style Engine variable sets into styling DOM
function aplicarCSSDinamico(cssCode) {
    const styleTag = document.getElementById("agnux-dynamic-theme");
    styleTag.innerHTML = cssCode;
}

// Sanitizes free AI-generated HTML: strips <script> so nothing executes
// outside the kernel's control (styles and inline markup remain intact).
function sanitizarHTMLLibre(html) {
    const tpl = document.createElement("template");
    tpl.innerHTML = html;
    tpl.content.querySelectorAll("script").forEach(s => s.remove());
    return tpl.content;
}

// Cascading spawn position so AI windows don't stack exactly on top of each other
let ventanasDinamicasCreadas = 0;

// 7. Dynamic Window Builder — supports free AI-generated HTML (windowSpec.html)
// or a chat-context window (windowSpec.content) as fallback.
function crearVentanaDinamica(windowSpec) {
    const desktop = document.getElementById("agnux-desktop");
    const winId = windowSpec["window-id"] || `win-${Date.now()}`;
    const esHTML = typeof windowSpec.html === "string" && windowSpec.html.trim() !== "";

    // Check if already exists → live update
    if (document.getElementById(winId)) {
        const win = document.getElementById(winId);
        const titleEl = win.querySelector(".window-title");
        if (titleEl) titleEl.textContent = windowSpec.title || "Ventana de Agnux";

        if (esHTML) {
            let htmlBody = win.querySelector(".window-html-content");
            if (!htmlBody) {
                // Was a chat window: convert its body to a free HTML surface
                const content = win.querySelector(".window-content");
                content.innerHTML = `<div class="window-html-content"></div>`;
                htmlBody = content.querySelector(".window-html-content");
            }
            htmlBody.replaceChildren(sanitizarHTMLLibre(windowSpec.html));
        } else {
            const logEl = win.querySelector(".window-chat-log");
            if (logEl) {
                const newMsg = document.createElement("div");
                newMsg.className = "message system-msg";
                newMsg.innerHTML = `<span class="sender">AGNUX:</span><p>${windowSpec.content || ""}</p>`;
                logEl.appendChild(newMsg);
            }
        }
        // openWindow togglea: solo re-mostrar si estaba oculta
        if (win.classList.contains("hidden")) openWindow(winId);
        return;
    }

    const win = document.createElement("div");
    win.id = winId;
    win.className = "agnux-window";
    const offset = (ventanasDinamicasCreadas++ % 6) * 32;
    win.style.top = `${140 + offset}px`;
    win.style.left = `${320 + offset}px`;
    win.style.width = esHTML ? "560px" : "480px";
    win.style.height = esHTML ? "440px" : "360px";

    const cuerpoVentana = esHTML
        ? `<div class="window-html-content"></div>`
        : `
            <div class="window-chat-log">
                <div class="message system-msg">
                    <span class="sender">AGNUX:</span>
                    <p>${windowSpec.content || "Ventana contextual de Agnux."}</p>
                </div>
            </div>
            <div class="stream-indicator hidden" style="padding: 10px 16px; font-size: 11px;">
                <span class="indicator-dot"></span> Procesando comando...
            </div>
            <div class="window-input-container">
                <input type="text" class="window-input" placeholder="Escribe en este contexto..." autocomplete="off">
                <button class="window-send-btn">Enviar</button>
            </div>
        `;

    win.innerHTML = `
        <div class="window-header">
            <div class="window-controls">
                <span class="control-dot close" onclick="document.getElementById('${winId}').remove()"></span>
                <span class="control-dot minimize" onclick="minimizeWindow('${winId}')"></span>
                <span class="control-dot expand" onclick="maximizeWindow('${winId}')"></span>
            </div>
            <span class="window-title">${windowSpec.title || "Ventana de Agnux"}</span>
        </div>
        <div class="window-content" style="display: flex; flex-direction: column; height: calc(100% - 40px); padding: 0;">
            ${cuerpoVentana}
        </div>
    `;

    if (esHTML) {
        win.querySelector(".window-html-content")
           .replaceChildren(sanitizarHTMLLibre(windowSpec.html));
    }

    desktop.appendChild(win);
    inicializarArrastreVentanas();

    if (!esHTML) {
        // Wire up events for this new dynamic window's chat input
        const input = win.querySelector(".window-input");
        const btn = win.querySelector(".window-send-btn");
        const enviarMsg = () => {
            const text = input.value.trim();
            if (text) {
                enviarPromptAlKernel(text, winId);
                input.value = "";
            }
        };
        btn.addEventListener("click", enviarMsg);
        input.addEventListener("keydown", (e) => {
            if (e.key === "Enter") enviarMsg();
        });
    }
}

// 8. Periodic Hardware Telemetry Polling
function comenzarMonitoreoTelemetry() {
    const cpuFill = document.getElementById("cpu-ring-fill");
    const ramFill = document.getElementById("ram-ring-fill");
    const cpuText = document.getElementById("cpu-val");
    const ramText = document.getElementById("ram-val");
    
    const statusQdrant = document.getElementById("status-qdrant");
    const statusOllama = document.getElementById("status-ollama");
    const statusDocker = document.getElementById("status-docker");
    const statusAiEngine = document.getElementById("status-ai-engine");
    const statusAiTokens = document.getElementById("status-ai-tokens");
    
    const poll = async () => {
        try {
            const res = await fetch(`${API_BASE}/api/system/status`);
            if (res.ok) {
                const data = await res.json();
                
                // Update CPU Ring Dash
                const cpuPercent = Math.round(data.hardware.cpu.usoPorcentaje);
                cpuText.textContent = `${cpuPercent}%`;
                const cpuOffset = 100 - cpuPercent;
                cpuFill.setAttribute("stroke-dasharray", `${cpuPercent}, 100`);
                
                // Update RAM Ring Dash
                const ramPercent = Math.round(data.hardware.memoria.porcentajeUso);
                ramText.textContent = `${ramPercent}%`;
                ramFill.setAttribute("stroke-dasharray", `${ramPercent}, 100`);
                
                // Update Status badges
                statusQdrant.textContent = data.hardware.estado === "OK" ? "Online" : "Offline";
                statusQdrant.className = data.hardware.estado === "OK" ? "val badge-success" : "val badge-error";
                
                statusOllama.textContent = "Online";
                statusOllama.className = "val badge-success";
                
                statusDocker.textContent = "Online";
                statusDocker.className = "val badge-success";
                
                // Update AI Engine Status & Tokens
                if (data.aiStats) {
                    const aiProv = data.aiStats.provider || "AI";
                    const aiStatus = data.aiStats.status || "Online";
                    statusAiEngine.textContent = `${aiProv.toUpperCase()} (${aiStatus})`;
                    
                    if (aiStatus === "Quota Exceeded") {
                        statusAiEngine.className = "val badge-warning";
                    } else if (aiStatus === "Error" || aiStatus === "Offline") {
                        statusAiEngine.className = "val badge-error";
                    } else {
                        statusAiEngine.className = "val badge-success";
                    }
                    
                    const totalTkn = data.aiStats.totalTokens || 0;
                    statusAiTokens.textContent = `${totalTkn} tkn`;
                }
            }
        } catch (e) {
            statusQdrant.textContent = "Offline";
            statusQdrant.className = "val badge-error";
            statusOllama.textContent = "Offline";
            statusOllama.className = "val badge-error";
            if (statusAiEngine) {
                statusAiEngine.textContent = "Offline";
                statusAiEngine.className = "val badge-error";
            }
        }
    };
    
    poll();
    setInterval(poll, 3000);
}
