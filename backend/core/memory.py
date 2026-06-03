import uuid
from datetime import datetime
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from core.config import qdrantHost, kernelLogger

# Initialize SentenceTransformer for embedding generation
try:
    from sentence_transformers import SentenceTransformer
    kernelLogger.info("🧠 [EMBEDDINGS] Cargando paraphrase-multilingual-mpnet-base-v2...")
    embeddingModel = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
except Exception as e:
    kernelLogger.error(f"❌ [EMBEDDINGS] Falla cargando SentenceTransformer: {e}")
    embeddingModel = None

# Async Qdrant Client
qdrantClient = AsyncQdrantClient(url=qdrantHost)

# Collections definitions
coleccionFacial = "perfiles_faciales"
coleccionMemoria = "agnux_kernel_memory"

# Global RAM cache structures in camelCase
cacheVectors = {
    "sistema": {},
    "usuarios": {}
}
temporaryFaceVectors = {}
terminalSessions = {}

def simularVectorRostro() -> list[float]:
    import random
    return [random.uniform(-1.0, 1.0) for _ in range(128)]

def generarVectorTexto(texto: str) -> list[float]:
    if embeddingModel is None:
        import random
        # Fallback to random vector (768 dimensions)
        return [random.uniform(-1.0, 1.0) for _ in range(768)]
    return embeddingModel.encode(texto).tolist()

async def guardarRecuerdoQdrant(userId: str, tipoEvento: str, contenido: str, metadataExtra: dict = None):
    try:
        if not contenido or len(contenido.strip()) < 3:
            return
        vectorValue = generarVectorTexto(contenido)
        pointId = str(uuid.uuid4())
        
        payloadData = {
            "userId": userId,
            "tipo": tipoEvento,
            "contenido": contenido,
            "timestamp": datetime.now().isoformat()
        }
        if metadataExtra:
            payloadData.update(metadataExtra)
            
        await qdrantClient.upsert(
            collection_name=coleccionMemoria,
            points=[PointStruct(id=pointId, vector=vectorValue, payload=payloadData)]
        )
        kernelLogger.info(f"💾 [QDRANT] Recuerdo semántico '{tipoEvento}' almacenado para {userId}.")
    except Exception as e:
        kernelLogger.error(f"❌ [QDRANT] Error al guardar recuerdo: {e}")

async def buscarRecuerdosQdrant(userId: str, queryText: str, limit: int = 3) -> list[dict]:
    try:
        vectorValue = generarVectorTexto(queryText)
        searchResults = await qdrantClient.query_points(
            collection_name=coleccionMemoria,
            query=vectorValue,
            query_filter=Filter(
                must=[FieldCondition(key="userId", match=MatchValue(value=userId))]
            ),
            limit=limit
        )
        
        memories = []
        for point in searchResults.points:
            memories.append({
                "contenido": point.payload.get("contenido", ""),
                "tipo": point.payload.get("tipo", ""),
                "score": point.score,
                "payload": point.payload
            })
        return memories
    except Exception as e:
        kernelLogger.error(f"❌ [QDRANT] Error al buscar recuerdos: {e}")
        return []

async def inicializarQdrantColecciones():
    kernelLogger.info("⚡ [QDRANT] Inicializando esquemas vectoriales...")
    try:
        collectionsInfo = await qdrantClient.get_collections()
        existingNames = [col.name for col in collectionsInfo.collections]
        
        if coleccionFacial not in existingNames:
            kernelLogger.info(f"🧠 Creando colección facial: {coleccionFacial}")
            await qdrantClient.create_collection(
                collection_name=coleccionFacial,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE)
            )
            
        if coleccionMemoria not in existingNames:
            kernelLogger.info(f"🧠 Creando colección de memoria: {coleccionMemoria}")
            await qdrantClient.create_collection(
                collection_name=coleccionMemoria,
                vectors_config=VectorParams(size=768, distance=Distance.COSINE)
            )
    except Exception as e:
        kernelLogger.error(f"❌ [QDRANT] Error inicializando colecciones: {e}")
