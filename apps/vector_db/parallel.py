from concurrent.futures import ThreadPoolExecutor, as_completed


class ParallelVectorDBWrapper:
    def __init__(self, base_db, max_workers=4):
        self.base_db = base_db
        self.max_workers = max_workers

    def sync(self, lazy_load_func, lazy_load_args):
        documents = list(lazy_load_func(*lazy_load_args))

        def process(doc):
            return doc  # you could preprocess here if needed

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(process, doc) for doc in documents]

            processed_docs = []
            for f in as_completed(futures):
                processed_docs.append(f.result())

        # reuse original sync
        return self.base_db.sync(lambda *_: processed_docs, [])

    def query(self, *args, **kwargs):
        return self.base_db.query(*args, **kwargs)
