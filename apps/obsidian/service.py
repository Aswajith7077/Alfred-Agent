from pathlib import Path
from vector_db import VectorDB
from langchain.tools import tool
from langchain_community.document_loaders import ObsidianLoader
from typing import Callable
from typing import Optional
from typing import Dict, Any, Generator
from agents import BaseTool

# Local Imports
from .models import Document


class Obsidian(BaseTool):
    """
    Obsidian vault loader with incremental indexing.

    Features:
    - Lazy loads documents on-demand
    - Detects file changes and skips unchanged files
    - Uses Custom Indexing for stateful indexing
    - Only syncs new/modified chunks to vector DB
    """

    def __init__(self, vault_path: str, db_service: VectorDB):
        super().__init__(self.__class__.__name__)
        self.vault_path = vault_path
        self.db_service = db_service
        self.loader = ObsidianLoader(vault_path)

    def __recursive_load_documents(
        self, path: Path, filter_fn: Optional[Callable] = None
    ) -> Generator[Document]:

        try:
            entries = sorted(path.iterdir())  # deterministic traversal
        except Exception as e:
            print(f"Cannot access {path}: {e}")
            return

        for entry in entries:
            if entry.is_dir() and entry.name not in [".git", ".obsidian"]:
                yield from self.__recursive_load_documents(entry, filter_fn=filter_fn)
                continue

            if entry.suffix != ".md":
                continue

            try:
                content = entry.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Skipping {entry}: {e}")
                continue

            document = Document(
                filename=str(entry),
                content=content,
                filesize=len(content),
                metadata={
                    "source": str(entry),
                    "filename": entry.name,
                    "folder": str(entry.parent),
                },
                images=None,
            )

            if filter_fn and not filter_fn(document):
                continue

            yield document

    def sync_to_vector_db(self) -> Dict[str, Any]:
        path = Path(self.vault_path)
        return self.db_service.sync(self.__recursive_load_documents, [path, None])

    def get_agent_tools(self):

        @tool
        def sync_to_vector_db() -> Dict[str, Any]:
            """
            Incremental sync to vector DB.
            Read the Obsidian Vault the user specified,
            Recursively load the files in a lazy load format.
            Then Storing the context into a vector store (Chroma in this case)
            Uses an Incremental Indexing, so only the required documents is loaded, avoids duplication


            - Detects unchanged files (skips them)
            - Computes chunk hashes for diffing
            - Deletes outdated chunks
            - Adds only new/modified chunks

            Returns sync statistics.
            """
            path = Path(self.vault_path)
            return self.db_service.sync(self.__recursive_load_documents, [path, None])

        @tool
        def search(query: str, k: int = 5) -> str:
            """
            A Search mechanism to search through the relevant content in the Knowledge base of the user
            Uses BM25 + Similarity Check for the retrieval augumentation
            The Docs are formatted at response
            These knowledgebase is literally an obsidian vault of the user
            """
            results = self.db_service.query(query, k=k)

            context_blocks = []

            for i, r in enumerate(results[:k]):
                block = f"""
[Document {i + 1}]
Source: {r["metadata"].get("filename", "")}

{r["content"]}
"""
                context_blocks.append(block)

            return "\n\n".join(context_blocks)

        return [sync_to_vector_db, search]
