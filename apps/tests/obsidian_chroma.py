from obsidian import Obsidian
from vector_db import VectorDB
from vector_db import BM25Ranker
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

# Initialize the service
vault_path = "C:\\Users\\Aswajith S\\OneDrive\\Documents\\ObsidianVault"
bm25_ranker = BM25Ranker()
vector_db = VectorDB(
    db_path="apps/vector_db/obsidian-db",
    embedding_model="nomic-embed-text",
    collection_name="obsidian_documents",
    bm25_ranker=bm25_ranker,
)
obsidian = Obsidian(vault_path=vault_path, db_service=vector_db)
obsidian.sync_to_vector_db()


r1 = obsidian.search("Nest JS Controllers, what are they")
# r2 = obsidian.search("What is Disjoint sets, how are they implemented in python")
# r3 = obsidian.search("How to implement binary search.")


pprint(obsidian.search("What is subdomain routing"))
