from .models import Document
from collections import Counter
from collections import defaultdict
from pathlib import Path
import numpy as np
import pickle


class BM25Ranker:
    STOPWORDS = {
        "the",
        "is",
        "at",
        "which",
        "on",
        "and",
        "a",
        "an",
        "to",
        "in",
        "of",
        "for",
        "with",
        "as",
        "by",
        "that",
        "this",
        "it",
        "from",
        "or",
        "be",
    }

    def __init__(self, k: float = 1.5, b: float = 0.75, persist_path: str = None):
        self.persist_path = persist_path
        self.k1 = k
        self.b = b

        # Try to load from disk first
        if self.persist_path and Path(self.persist_path).exists():
            self._load()
        else:
            self._init_empty()

    def _init_empty(self):
        self.documents = []
        self.average_length = 0
        self.docs_count = 0
        self.document_freq = defaultdict(int)
        self.distinct_words = set()
        self.document_lengths = defaultdict()
        self.document_counters = {}
        self.scores = defaultdict(lambda: defaultdict(float))

    def _save(self):
        """Persist BM25 index to disk."""
        if not self.persist_path:
            return
        path = Path(self.persist_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Convert defaultdicts to regular dicts for pickling
        data = {
            "documents": self.documents,
            "average_length": self.average_length,
            "docs_count": self.docs_count,
            "document_freq": dict(self.document_freq),
            "distinct_words": self.distinct_words,
            "document_lengths": dict(self.document_lengths),
            "document_counters": self.document_counters,
            "scores": {
                doc_id: dict(word_scores) for doc_id, word_scores in self.scores.items()
            },
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def _load(self):
        """Load BM25 index from disk."""
        try:
            with open(self.persist_path, "rb") as f:
                data = pickle.load(f)

            self.documents = data["documents"]
            self.average_length = data["average_length"]
            self.docs_count = data["docs_count"]
            self.document_freq = defaultdict(int, data["document_freq"])
            self.distinct_words = data["distinct_words"]
            self.document_lengths = defaultdict(None, data["document_lengths"])
            self.document_counters = data["document_counters"]

            # Restore nested defaultdicts
            self.scores = defaultdict(lambda: defaultdict(float))
            for doc_id, word_scores in data["scores"].items():
                for word, score in word_scores.items():
                    self.scores[doc_id][word] = score

            print(
                f"✓ Loaded BM25 index ({self.docs_count} documents) from {self.persist_path}"
            )
        except Exception as e:
            print(f"⚠ Failed to load BM25 index: {e}, starting fresh")
            self._init_empty()

    def preprocess_content(self, content):

        content = content.lower()
        content = "".join([ch for ch in content if ch.isalpha() or ch == " "])

        return [token for token in content.split() if token not in BM25Ranker.STOPWORDS]

    def add(self, document: Document):

        # Prepend filename (title) to content so BM25 indexes title words too.
        # In Obsidian, the filename IS the title and the body often doesn't repeat it.
        title = Path(document.filename).stem
        raw_content = title + " " + document.content
        corpus = self.preprocess_content(raw_content)
        counter = Counter(corpus)

        distinct_words = set(corpus)

        if document.filename not in self.document_lengths:
            self.docs_count += 1
            self.average_length = (
                self.average_length
                + (document.filesize - self.average_length) / self.docs_count
            )
        else:
            old_size = self.document_lengths[document.filename]
            self.average_length += (document.filesize - old_size) / self.docs_count
            for word in self.document_counters[document.filename]:
                self.document_freq[word] -= 1

            self.scores[document.filename].clear()

        self.document_lengths[document.filename] = document.filesize
        self.document_counters[document.filename] = counter

        for word in distinct_words:
            self.distinct_words.add(word)
            self.document_freq[word] += 1

        for word in distinct_words:  # words whose df/idf changed
            df = self.document_freq[word]
            idf = np.log(1 + (self.docs_count - df + 0.5) / (df + 0.5))

            for doc_id, doc_length in self.document_lengths.items():
                f = self.document_counters[doc_id][word]
                if f == 0:
                    self.scores[doc_id][word] = 0.0
                    continue
                numerator = f * (self.k1 + 1)
                denominator = f + self.k1 * (
                    1 - self.b + self.b * doc_length / self.average_length
                )
                self.scores[doc_id][word] = idf * numerator / denominator

    def save(self):
        """Public method to trigger persistence after a sync completes."""
        self._save()

    def get_scores(self, document_id):
        return self.scores[document_id]
