import os
import json
import chromadb
from sentence_transformers import SentenceTransformer

DATA_FOLDER = "data"

personas = []

for file_name in os.listdir(DATA_FOLDER):
    if file_name.endswith(".json"):

        file_path = os.path.join(DATA_FOLDER, file_name)

        with open(file_path, "r", encoding="utf-8") as f:
            persona = json.load(f)
            personas.append(persona)

print(f"\nToplam {len(personas)} adet persona bulundu.\n")

for persona in personas:
    print(
        f"{persona['patient_id']} - {persona['metadata']['full_name']}"
    )
documents = []
metadatas = []
ids = []
for persona in personas:

    patient_id = persona["patient_id"]
    for memory in persona["core_memories"]:

        documents.append(memory["content"])

        ids.append(memory["memory_id"])

        metadatas.append({
            "patient_id": patient_id,
            "type": "memory",
            "category": memory["category"]
        })
    for i, routine in enumerate(persona["daily_routines"]):

        text = f"{routine['time']} - {routine['activity']}. {routine['description']}"

        documents.append(text)

        ids.append(f"{patient_id}-routine-{i}")

        metadatas.append({
            "patient_id": patient_id,
            "type": "routine"
        })
print(f"\nToplam belge sayısı: {len(documents)}\n")

for doc in documents[:10]:
    print(doc)    
print("\nEmbedding modeli yükleniyor...")

model = SentenceTransformer("all-MiniLM-L6-v2")

print("Embedding oluşturuluyor...")

embeddings = model.encode(documents)

print(f"Toplam embedding sayısı: {len(embeddings)}")
print(f"Bir embedding boyutu: {len(embeddings[0])}")                    
print("\nChromaDB oluşturuluyor...")

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_or_create_collection(
    name="patient_memories"
)
collection.add(
    ids=ids,
    documents=documents,
    embeddings=embeddings.tolist(),
    metadatas=metadatas
)
print(f"\nToplam kayıt sayısı: {collection.count()}")