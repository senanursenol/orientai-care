import os
import json
from db_config import chroma_collection

# Sentetik hasta personaları repo kökündeki data/synthetic_personas/ altında yaşar
_REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
DATA_FOLDER = os.path.join(_REPO_ROOT, "data", "synthetic_personas")
personas = []

for file_name in os.listdir(DATA_FOLDER):
    if file_name.endswith(".json") and file_name != "persona_schema.json":
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

for persona in personas:
    patient_id = persona["patient_id"]
    
  
    for memory in persona["core_memories"]:
        documents.append(memory["content"])
        ids.append(memory["memory_id"])
        
        # Liste olan keywords yapısını düz metne (string) çeviriyoruz
        keywords_str = ", ".join(memory.get("keywords", []))
        
        metadatas.append({
            "patient_id": patient_id,
            "type": "memory",
            "category": memory.get("category", "general"),
            "keywords": keywords_str  # Destek eklendi
        })
        
    
    for i, routine in enumerate(persona["daily_routines"]):
        text = f"{routine['time']} - {routine['activity']}. {routine['description']}"
        documents.append(text)
        ids.append(f"{patient_id}-routine-{i}")
        
       
        routine_keywords = routine.get("reminder_type", routine["activity"])
        
        metadatas.append({
            "patient_id": patient_id,
            "type": "routine",
            "category": "routine",      
            "keywords": routine_keywords 
        })



print(f"\nToplam belge sayısı: {len(documents)}\n")

for doc in documents[:10]:
    print(doc)    


# ChromaDB, db_config.py otomatik vektörleştirilecek

print("\nChromaDB'ye veriler modelinizle otomatik aktarılıyor...")


chroma_collection.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas
)

print(f"\nVeritabanındaki toplam kayıt sayısı: {chroma_collection.count()}")
