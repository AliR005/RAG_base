import hashlib
from os import listdir

from chromadb import PersistentClient
from chromadb.api.types import EmbeddingFunction
from config import settings
from sentence_transformers import SentenceTransformer


class CustomEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model):
        self.model = model

    def __call__(self, input):
        return self.model.encode(input).tolist()


class VectorStore:
    def __init__(self):
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.embedding_function = CustomEmbeddingFunction(self.model)
        self.client = PersistentClient(path=settings.CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(
            settings.COLLECTION_NAME, embedding_function=self.embedding_function
        )

    def load_docs(self, directory: str):
        from doc_processor import read_docx_and_split

        files_paths = [
            f"{directory}/{filename}"
            for filename in listdir(directory)
            if filename.endswith(".docx")
        ]
        for path in files_paths:
            chunks = read_docx_and_split(path)
            if chunks:
                file_hash = hashlib.md5(path.encode()).hexdigest()[:8]
                ids = [
                    f"{path[8:]}&{file_hash}_{i}" for i in range(len(chunks))
                ]
                self.collection.add(documents=chunks, ids=ids)
                print(ids, chunks, "\n\n\n")
                print(f"Processed {path}: {len(chunks)} chunks")

    def find_relevant_context(self, query_embedding, top_k=5):

        query_embedding_list = query_embedding.tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding_list], n_results=top_k
        )
        if results["documents"]:
            return results["ids"][0], results["documents"][0]
        else:
            return [], []
