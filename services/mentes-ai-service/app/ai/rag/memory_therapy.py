from services.memory_service import (
    retrieve_memories,
    generate_memory_response,
)

def analyze_photo(photo_path):
    """
    İleride Vision modeli bu fonksiyonda çağrılacak.

    Döndürülecek örnek format:

    {
        "person": "...",
        "objects": [...],
        "context": "..."
    }
    """
    pass
patient_id = "P-1001"

photo_path = "sample_photo.jpg"

print("Fotoğraf analiz ediliyor...\n")

vision_result = {
    "person": "Zeynep",
    "objects": [
        "flowers",
        "wheelchair",
        "tree"
    ],
    "context": "garden"
}

memories = retrieve_memories(
    patient_id,
    vision_result
)

response = generate_memory_response(memories)
print("Asistanın Cevabı:\n")
print(response)