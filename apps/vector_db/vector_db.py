from obsidian.index import IndexState
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import Any
from typing import Callable
from typing import List
from utils import compute_hash
from pathlib import Path
from .bm25_wrapper import BM25Ranker
from .models import Document

BASE_DIR = Path(__file__).resolve().parent.parent


class VectorDB:
    def __init__(
        self,
        db_path: str,
        collection_name: str,
        bm25_ranker:BM25Ranker,
        embedding_model: str = "nomic-embed-text",
    ):

        self.db_path = db_path
        self.index_path = BASE_DIR / "obsidian" / "indexes" / "index_state.json"
        self.embeddings = OllamaEmbeddings(model=embedding_model,base_url="http://127.0.0.1:11434")
        self.db = Chroma(
            persist_directory=db_path,
            embedding_function=self.embeddings,
            collection_name=collection_name,
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        )
        self.bm25_ranker = bm25_ranker

    def sync(
        self,
        lazy_load_func: Callable,
        lazy_load_args: List[Callable],
        batch_size: int = 64,
    ) -> None:

        batch = []
        count = 0
        state = IndexState(self.index_path)

        for document in lazy_load_func(*lazy_load_args):
            file_id = document.filename
            content_hash = compute_hash(document.content)

            self.bm25_ranker.add(document)
            if file_id in state.state and state.state[file_id] == content_hash:
                continue

            self.db.delete(where={"source": file_id})
            metadata = dict[str, Any](document.metadata)
            metadata["source"] = file_id
            metadata["images"] = document.images
            chunks = self.text_splitter.create_documents(
                [document.content], metadatas=[metadata]
            )

            batch.extend(chunks)
            count += 1

            state.state[file_id] = content_hash

            if len(batch) >= batch_size:
                ids = [compute_hash(doc.page_content) for doc in batch]
                self.db.add_documents(batch, ids=ids)
                print(f"✓ Synced {len(batch)} chunks from {count} documents")
                batch = []

        if batch:
            self.db.add_documents(batch)
            print(f"✓ Synced final {len(batch)} chunks from {count} documents")

        state.save()

        print(f"✓ Total: {count} documents synced to vector DB at {self.db_path}")

    def query(self, query: str, k: int = 10,alpha:float = 0.5) -> List[(Document, dict,float)]:

        similarity_results = self.db.similarity_search_with_score(query, k=k)
        preprocessed_query = self.bm25_ranker.preprocess_content(query)

        results = []
        print(similarity_results[0])
        for doc, similarity_score in similarity_results:

            filename = doc.metadata['source']

            bm25_scores = self.bm25_ranker.get_scores(filename)
            bm25_score = sum(bm25_scores[t] for t in preprocessed_query)
            final_score = (1 - alpha) * similarity_score + alpha * bm25_score


            print(f'BM25 Score: {bm25_score}, Similarity Score: {similarity_score}')

            record = [filename,doc.metadata,final_score]
            results.append(record)
        
        return results


