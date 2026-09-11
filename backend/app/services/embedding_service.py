import os
import json
import pickle
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings

settings = get_settings()
INDEX_DIR = "vector_indices"


class EmbeddingService:
    _model = None

    @classmethod
    def get_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        return cls._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self.get_model()
        return model.encode(texts, normalize_embeddings=True)

    def _get_index_path(self, business_id: str):
        path = os.path.join(INDEX_DIR, business_id)
        os.makedirs(path, exist_ok=True)
        return path

    def add_to_index(self, business_id: str, chunks: list[str], embeddings: np.ndarray, doc_ids: list[str]):
        path = self._get_index_path(business_id)
        index_file = os.path.join(path, "index.faiss")
        meta_file = os.path.join(path, "metadata.pkl")

        dim = embeddings.shape[1]

        if os.path.exists(index_file):
            index = faiss.read_index(index_file)
            with open(meta_file, "rb") as f:
                metadata = pickle.load(f)
        else:
            index = faiss.IndexFlatIP(dim)
            metadata = {"chunks": [], "doc_ids": []}

        index.add(embeddings.astype(np.float32))
        metadata["chunks"].extend(chunks)
        metadata["doc_ids"].extend(doc_ids)

        faiss.write_index(index, index_file)
        with open(meta_file, "wb") as f:
            pickle.dump(metadata, f)

    def search(self, business_id: str, query: str, top_k: int = 5) -> list[dict]:
        path = self._get_index_path(business_id)
        index_file = os.path.join(path, "index.faiss")
        meta_file = os.path.join(path, "metadata.pkl")

        if not os.path.exists(index_file):
            return []

        index = faiss.read_index(index_file)
        with open(meta_file, "rb") as f:
            metadata = pickle.load(f)

        query_vec = self.encode([query]).astype(np.float32)
        scores, indices = index.search(query_vec, min(top_k, index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            results.append({
                "chunk": metadata["chunks"][idx],
                "doc_id": metadata["doc_ids"][idx],
                "score": float(score),
            })
        return results

    def remove_document(self, business_id: str, document_id: str):
        path = self._get_index_path(business_id)
        index_file = os.path.join(path, "index.faiss")
        meta_file = os.path.join(path, "metadata.pkl")

        if not os.path.exists(index_file):
            return

        index = faiss.read_index(index_file)
        with open(meta_file, "rb") as f:
            metadata = pickle.load(f)

        keep_indices = [i for i, did in enumerate(metadata["doc_ids"]) if did != document_id]

        if not keep_indices:
            os.remove(index_file)
            os.remove(meta_file)
            return

        new_chunks = [metadata["chunks"][i] for i in keep_indices]
        new_doc_ids = [metadata["doc_ids"][i] for i in keep_indices]
        new_embeddings = self.encode(new_chunks)

        dim = new_embeddings.shape[1]
        new_index = faiss.IndexFlatIP(dim)
        new_index.add(new_embeddings.astype(np.float32))

        faiss.write_index(new_index, index_file)
        with open(meta_file, "wb") as f:
            pickle.dump({"chunks": new_chunks, "doc_ids": new_doc_ids}, f)
