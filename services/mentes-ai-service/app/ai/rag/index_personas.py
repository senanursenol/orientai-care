import os
import json
from db_config import chroma_collection
current_dir = os.path.dirname(os.path.abspath(__file__))

DATA_FOLDER = os.path.join(current_dir, "..", "data")
personas = []

# Persona dosyalarını oku
for file_name in os.listdir(DATA_FOLDER):
    if file_name.endswith(".json"):
        file_path = os.path.join(DATA_FOLDER, file_name)

        with open(file_path, "r", encoding="utf-8") as f:
            persona = json.load(f)
            personas.append(persona)

print(f"\nToplam {len(personas)} adet persona bulundu.\n")

for persona in personas:
    print(f"{persona['patient_id']} - {persona['metadata']['full_name']}")

documents = []
metadatas = []
ids = []

# Persona verilerini ChromaDB formatına dönüştür
for persona in personas:

    patient_id = persona["patient_id"]

    # -----------------------------
    # Core Memories
    # -----------------------------
    for memory in persona["core_memories"]:

        keywords = memory.get("keywords", [])
        keywords_str = ", ".join(keywords)

        document = f"""
Category: {memory.get("category", "general")}
Keywords: {keywords_str}

Memory:
{memory["content"]}
""".strip()

        documents.append(document)
        ids.append(memory["memory_id"])

        metadatas.append({
            "patient_id": patient_id,
            "type": "memory",
            "category": memory.get("category", "general"),
            "keywords": keywords_str
        })

    # -----------------------------
    # Daily Routines
    # -----------------------------
    for i, routine in enumerate(persona["daily_routines"]):

        routine_keywords = routine.get(
            "reminder_type",
            routine["activity"]
        )

        document = f"""
Category: routine
Keywords: {routine_keywords}

Routine

Time: {routine['time']}
Activity: {routine['activity']}
Description: {routine['description']}
""".strip()

        documents.append(document)

        ids.append(f"{patient_id}-routine-{i}")

        metadatas.append({
            "patient_id": patient_id,
            "type": "routine",
            "category": "routine",
            "keywords": routine_keywords
        })

print(f"\nToplam belge sayısı: {len(documents)}\n")

print("İlk 5 belge:\n")

for doc in documents[:5]:
    print(doc)
    print("-" * 60)

print("\nChromaDB'ye veriler aktarılıyor...")

chroma_collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)

print(f"\nVeritabanındaki toplam kayıt sayısı: {chroma_collection.count()}")

