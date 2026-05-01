from pathlib import Path
from vector_db import VectorDB
from langchain_community.document_loaders import ObsidianLoader
from typing import Callable
from typing import Optional
from typing import Dict, Any, List, Generator

# Local Imports
from .models import Document


class Obsidian:
    """
    Obsidian vault loader with incremental indexing.

    Features:
    - Lazy loads documents on-demand
    - Detects file changes and skips unchanged files
    - Uses Custom Indexing for stateful indexing
    - Only syncs new/modified chunks to vector DB
    """

    def __init__(self, vault_path: str, db_service: VectorDB):
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

    def sync_to_vector_db(
        self, filter_function: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Incremental sync to vector DB.

        LangChain's SQLRecordManager automatically:
        - Detects unchanged files (skips them)
        - Computes chunk hashes for diffing
        - Deletes outdated chunks
        - Adds only new/modified chunks

        Returns sync statistics.
        """
        path = Path(self.vault_path)
        return self.db_service.sync(
            self.__recursive_load_documents, [path, filter_function]
        )

    def search(self, query: str, k: int = 5) -> List:
        """Search all indexed documents."""
        return self.db_service.query(query, k=k)
