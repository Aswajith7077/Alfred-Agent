from .models import Document
from collections import Counter
from collections import defaultdict
import numpy as np

class BM25Ranker:
    STOPWORDS = {
        "the","is","at","which","on","and","a","an","to","in","of",
        "for","with","as","by","that","this","it","from","or","be"
    }

    def __init__(self,k:float = 1.5,b:float = 0.75):
        self.documents = []
        self.k1 = k
        self.b = b
        self.average_length = 0
        self.docs_count = 0
        self.document_freq = defaultdict(int)
        self.distinct_words = set()
        self.document_lengths = defaultdict()
        self.document_counters = {}

        self.scores = defaultdict(lambda : defaultdict(float))

    def preprocess_content(self,content):

        content = content.lower()
        content = "".join([ch for ch in content if ch.isalpha() or ch == ' '])
        
        return [token for token in content.split() if token not in BM25Ranker.STOPWORDS]
        

    def add(self,document:Document):

        raw_content = document.content
        corpus = self.preprocess_content(raw_content)
        counter = Counter(corpus)

        distinct_words = set(corpus)

        if document.filename not in self.document_lengths:
            self.docs_count += 1
            self.average_length = self.average_length + (document.filesize - self.average_length) / self.docs_count
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

        for word in distinct_words:
            for doc,n in self.document_lengths.items():

                df = self.document_freq[word]
                f = self.document_counters[doc][word]
                numerator = f * (self.k1 + 1)
                denominator = f + self.k1 * ( 1 - self.b + self.b * n / self.average_length)

                idf = np.log(1 + (self.docs_count - df + 0.5) / (df + 0.5))

                score = idf * numerator / denominator

                self.scores[doc][word] = score

    def get_scores(self,document_id):
        return self.scores[document_id]
