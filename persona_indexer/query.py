import chromadb
from sentence_transformers import SentenceTransformer

# Aynı embedding modelini yükle
model = SentenceTransformer("all-MiniLM-L6-v2")

# ChromaDB'ye bağlan
client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_collection("patient_memories")
patient_id=input("Hasta ID:")
# Kullanıcının sorusunu al
question = input("Sorunuzu girin: ")

# Soruyu embedding'e dönüştür
question_embedding = model.encode(question)

# En benzer belgeyi ara
results = collection.query(
    query_embeddings=[question_embedding.tolist()],
    n_results=1,
    where={"patient_id": patient_id}
)

print("\nSonuçlar:\n")

for document, metadata in zip(
    results["documents"][0],
    results["metadatas"][0]
):
    print(metadata)
    print(document)
    print("-" * 40)