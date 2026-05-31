import uuid
from datetime import datetime
import asyncio
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from core.config import logger, QDRANT_HOST

try:
    from sentence_transformers import SentenceTransformer
    logger.info("🧠 [EMBEDDINGS] Cargando modelo semántico en CPU (paraphrase-multilingual-mpnet-base-v2)...")
    embedding_model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
except Exception as e:
    logger.error(f"❌ [EMBEDDINGS] Falla al cargar SentenceTransformer: {e}")
    embedding_model = None

# Cliente de Qdrant
qdrant_client = AsyncQdrantClient(url=QDRANT_HOST)

# Constantes de colecciones
COLECCION_FACIAL = "perfiles_faciales"
COLECCION_MEMORIA = "agnux_kernel_memory"

# =====================================================================
# MATRICES DE MEMORIA GLOBAL (RAM KERNEL)
# =====================================================================
CACHE_VECTORS = {
    "sistema": {},
    "usuarios": {}
}

# Semáforo FIFO asíncrono para evitar saturar el bus de inferencia
OLLAMA_BUS_LOCK = asyncio.Lock()

# Volátil para enrolamiento de rostros no registrados
TEMPORARY_FACE_VECTORS = {}

# Mapeo de terminales físicas (monitores sin cámara esperando al celular)
TERMINAL_SESSIONS = {}

def simular_vector_rostro() -> list[float]:
    import random
    return [random.uniform(-1.0, 1.0) for _ in range(128)]

def generar_vector_texto(texto: str) -> list[float]:
    if embedding_model is None:
        import random
        return [random.uniform(-1.0, 1.0) for _ in range(768)]
    return embedding_model.encode(texto).tolist()

async def guardar_recuerdo_qdrant(user_id: str, tipo_evento: str, contenido: str, metadata_extra: dict = None):
    try:
        if not contenido or len(contenido.strip()) < 3: return
        vector = generar_vector_texto(contenido)
        point_id = str(uuid.uuid4())
        
        payload = {
            "user-id": user_id,
            "tipo": tipo_evento,
            "contenido": contenido,
            "timestamp": datetime.now().isoformat()
        }
        if metadata_extra:
            payload.update(metadata_extra)
            
        await qdrant_client.upsert(
            collection_name=COLECCION_MEMORIA,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)]
        )
        logger.info(f"💾 [MEMORIA] Recuerdo semántico ({tipo_evento}) almacenado para {user_id}.")
    except Exception as e:
        logger.error(f"❌ [MEMORIA] Error al guardar recuerdo: {e}")

async def inicializar_qdrant_colecciones():
    logger.info("⚡ [KERNEL BOOT] Inicializando servicios base de memoria persistente...")
    try:
        collections_response = await qdrant_client.get_collections()
        collection_names = [col.name for col in collections_response.collections]
        
        if COLECCION_FACIAL not in collection_names:
            logger.info(f"🧠 [QDRANT] Creando colección '{COLECCION_FACIAL}' (128d, COSINE)...")
            await qdrant_client.create_collection(
                collection_name=COLECCION_FACIAL,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
            
        if COLECCION_MEMORIA not in collection_names:
            logger.info(f"🧠 [QDRANT] Creando colección '{COLECCION_MEMORIA}' (768d, COSINE)...")
            await qdrant_client.create_collection(
                collection_name=COLECCION_MEMORIA,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
    except Exception as e:
        logger.error(f"❌ [QDRANT] Falla al inicializar bus vectorial: {e}")
