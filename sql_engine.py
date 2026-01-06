import os

# Disable telemetry before any chromadb imports
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["POSTHOG_DISABLED"] = "1"
os.environ["CHROMA_TELEMETRY"] = "False"

from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from config import OPENAI_API_KEY, OPENAI_MODEL, CHROMA_PERSIST_DIR, EMBEDDING_MODEL


class LocalEmbeddingFunction:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self._model = SentenceTransformer(model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        embeddings = self._model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()


class TextToSQL(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, api_key: str = None):
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

        self._embedding_function = LocalEmbeddingFunction()
        self._chroma_client = chromadb.PersistentClient(
            path=str(CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )

        ChromaDB_VectorStore.__init__(
            self,
            config={
                "client": self._chroma_client,
                "embedding_function": self._embedding_function,
            },
        )
        
        effective_key = api_key or OPENAI_API_KEY
        OpenAI_Chat.__init__(
            self,
            config={
                "api_key": effective_key,
                "model": OPENAI_MODEL,
            },
        )

    def get_training_data_count(self) -> dict:
        counts = {"ddl": 0, "documentation": 0, "questions": 0}
        try:
            ddl_collection = self._chroma_client.get_collection("ddl")
            counts["ddl"] = ddl_collection.count()
        except Exception:
            pass
        try:
            doc_collection = self._chroma_client.get_collection("documentation")
            counts["documentation"] = doc_collection.count()
        except Exception:
            pass
        try:
            sql_collection = self._chroma_client.get_collection("sql")
            counts["questions"] = sql_collection.count()
        except Exception:
            pass
        return counts


_engine_cache = {}


def get_engine(api_key: str = None) -> TextToSQL:
    cache_key = api_key or "default"
    if cache_key not in _engine_cache:
        _engine_cache[cache_key] = TextToSQL(api_key=api_key)
    return _engine_cache[cache_key]
