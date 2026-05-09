from config import Settings
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

BASE_DIR = Path(__file__).resolve().parent.parent


class VectorDB:
    def __init__(
        self,
        settings: Settings,
        bm25_ranker: BM25Ranker,
        embedding_model: str = "nomic-embed-text",
    ):

        self.db_path = settings.VECTOR_DB_PATH
        # Prefer the explicit index-state path if present; fall back for older Settings.
        self.index_path = getattr(settings, "INDEX_STATE_PATH", settings.STATE_PATH)
        self.embeddings = OllamaEmbeddings(
            model=embedding_model, base_url=settings.OLLAMA_URL
        )
        self.db = Chroma(
            persist_directory=settings.VECTOR_DB_PATH,
            embedding_function=self.embeddings,
            collection_name=settings.COLLECTION_NAME,
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
        self.bm25_ranker.save()

        print(f"✓ Total: {count} documents synced to vector DB at {self.db_path}")

    def query(self, query: str, k: int = 10, alpha: float = 0.5) -> List:

        # Fetch more chunks from Chroma to have better coverage per document
        fetch_k = k * 3
        similarity_results = self.db.similarity_search_with_score(query, k=fetch_k)
        preprocessed_query = self.bm25_ranker.preprocess_content(query)
        query_terms_set = set(preprocessed_query)

        # Build a map of source -> best chunk info
        # For each source, keep the chunk with best similarity AND the chunk with best keyword overlap
        results_map = {}
        keyword_chunks = {}  # source -> (content, metadata, keyword_hit_count)

        for doc, raw_similarity_score in similarity_results:
            filename = doc.metadata["source"]
            similarity_score = 1 / (1 + raw_similarity_score)

            # Keep the best chunk per source by similarity
            if (
                filename not in results_map
                or similarity_score > results_map[filename]["similarity_score"]
            ):
                results_map[filename] = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": similarity_score,
                }

            # Also track the chunk with best keyword overlap per source
            chunk_tokens = set(self.bm25_ranker.preprocess_content(doc.page_content))
            keyword_hits = len(query_terms_set & chunk_tokens)
            if keyword_hits > 0:
                if (
                    filename not in keyword_chunks
                    or keyword_hits > keyword_chunks[filename]["keyword_hits"]
                ):
                    keyword_chunks[filename] = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": similarity_score,
                        "keyword_hits": keyword_hits,
                    }

        # Also get BM25 top-k candidates (documents with highest BM25 scores for this query)
        bm25_candidates = self._get_bm25_top_k(preprocessed_query, k=k)

        for filename, bm25_score in bm25_candidates:
            if filename not in results_map:
                # Fetch multiple chunks from Chroma for this BM25-matched document
                try:
                    chroma_docs = self.db.similarity_search_with_score(
                        query, k=5, filter={"source": filename}
                    )
                    best_sim = None
                    best_kw = None
                    for doc, raw_score in chroma_docs:
                        sim_score = 1 / (1 + raw_score)
                        if best_sim is None or sim_score > best_sim["similarity_score"]:
                            best_sim = {
                                "content": doc.page_content,
                                "metadata": doc.metadata,
                                "similarity_score": sim_score,
                            }
                        # Check keyword overlap
                        chunk_tokens = set(
                            self.bm25_ranker.preprocess_content(doc.page_content)
                        )
                        kw_hits = len(query_terms_set & chunk_tokens)
                        if kw_hits > 0 and (
                            best_kw is None or kw_hits > best_kw["keyword_hits"]
                        ):
                            best_kw = {
                                "content": doc.page_content,
                                "metadata": doc.metadata,
                                "similarity_score": sim_score,
                                "keyword_hits": kw_hits,
                            }

                    if best_sim:
                        results_map[filename] = best_sim
                    if best_kw:
                        keyword_chunks[filename] = best_kw
                except Exception:
                    pass

        # Now compute final hybrid scores
        results = []
        for filename, data in results_map.items():
            bm25_scores = self.bm25_ranker.get_scores(filename)
            bm25_score = sum(bm25_scores[t] for t in preprocessed_query)
            similarity_score = data["similarity_score"]

            # If this document has a significant BM25 score AND a keyword-matching chunk,
            # use the keyword chunk instead — it's more likely to contain the relevant content
            content = data["content"]
            metadata = data["metadata"]
            if bm25_score > 0 and filename in keyword_chunks:
                content = keyword_chunks[filename]["content"]
                metadata = keyword_chunks[filename]["metadata"]

            final_score = (1 - alpha) * similarity_score + alpha * bm25_score

            print(
                f"BM25 Score: {bm25_score:.4f}, Similarity Score: {similarity_score:.4f}, Source: {metadata.get('filename', '')}"
            )

            record = {
                "content": content,
                "metadata": metadata,
                "score": final_score,
            }
            results.append(record)

        # Sort by final score descending and return top-k
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[:k]

    def _get_bm25_top_k(self, preprocessed_query: list, k: int = 8) -> list:
        """Get top-k documents by BM25 score for the given preprocessed query."""
        doc_scores = []
        for doc_id in self.bm25_ranker.scores:
            scores = self.bm25_ranker.get_scores(doc_id)
            total = sum(scores[t] for t in preprocessed_query)
            if total > 0:
                doc_scores.append((doc_id, total))

        doc_scores.sort(key=lambda x: x[1], reverse=True)
        return doc_scores[:k]
