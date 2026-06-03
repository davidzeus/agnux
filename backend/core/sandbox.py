import docker
import time
from core.config import kernelLogger

def evaluarCodigoSandbox(codigo: str, lenguaje: str = "python") -> dict:
    kernelLogger.info(f"🐳 [SANDBOX] Iniciando validación de código [{lenguaje}]...")
    try:
        dockerClient = docker.from_env()
    except Exception as e:
        kernelLogger.error(f"❌ [SANDBOX] Error conectando a Docker daemon: {e}")
        return {
            "ok": False,
            "output": f"Docker daemon connection failed: {e}",
            "executionTimeMs": 0,
            "exitCode": -1
        }
        
    if lenguaje.strip().lower() != "python":
        return {
            "ok": False,
            "output": f"Unsupported language: {lenguaje}",
            "executionTimeMs": 0,
            "exitCode": -1
        }
        
    containerName = f"agnux-sandbox-{int(time.time())}"
    startTime = time.time()
    
    try:
        # Launching an isolated container executing python -c "code"
        # We pass code via environment variable or command to avoid quoting issues
        container = dockerClient.containers.run(
            image="python:3.11-alpine",
            command=["python", "-c", codigo],
            name=containerName,
            network_mode="none", # Completely isolated, no internet access inside sandbox
            mem_limit="128m",    # Cap memory usage
            nano_cpus=500000000, # Cap CPU to 0.5 core
            detach=True
        )
        
        # Wait for container execution with a timeout of 10 seconds
        result = container.wait(timeout=10)
        executionTimeMs = int((time.time() - startTime) * 1000)
        
        exitCode = result.get("StatusCode", -1)
        outputBytes = container.logs(stdout=True, stderr=True)
        outputText = outputBytes.decode("utf-8", errors="replace")
        
        container.remove(force=True)
        
        if exitCode == 0:
            kernelLogger.info(f"✅ [SANDBOX] Código aprobado en {executionTimeMs}ms.")
            return {
                "ok": True,
                "output": outputText,
                "executionTimeMs": executionTimeMs,
                "exitCode": exitCode
            }
        else:
            kernelLogger.warning(f"⚠️ [SANDBOX] Código fallido con exit code {exitCode}.")
            return {
                "ok": False,
                "output": outputText,
                "executionTimeMs": executionTimeMs,
                "exitCode": exitCode
            }
            
    except Exception as e:
        executionTimeMs = int((time.time() - startTime) * 1000)
        kernelLogger.error(f"❌ [SANDBOX] Falla crítica durante ejecución: {e}")
        try:
            # Cleanup container if left running
            container = dockerClient.containers.get(containerName)
            container.remove(force=True)
        except Exception:
            pass
            
        return {
            "ok": False,
            "output": f"Sandbox execution crash/timeout: {e}",
            "executionTimeMs": executionTimeMs,
            "exitCode": -1
        }
