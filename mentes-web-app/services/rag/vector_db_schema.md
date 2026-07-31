# OrientAI Vektör Veritabanı (ChromaDB) Koleksiyon Şeması

Bu döküman, `persona_indexer` projesindeki yapay zeka hafızasının veri yapısını ve koleksiyon planını tanımlar.

## Koleksiyon Bilgileri
- **Koleksiyon Adı:** `patient_memories`
- **Embedding Modeli:** `all-MiniLM-L6-v2` (SentenceTransformers)
- **Vektör Boyutu:** 384 Dimensions

## Kayıt (Segment) Yapısı

ChromaDB üzerinde saklanan her bir vektör kaydı aşağıdaki hiyerarşiye uygun olarak yüklenir:

### 1. Core Memories (Çekirdek Anılar) Segmenti
- **ID:** `[memory_id]` (Örn: `m-101`)
- **Document:** `memory["content"]` (Anının ham hikaye metni)
- **Metadata:**
  ```json
  {
    "patient_id": "P-XXXX",
    "type": "memory",
    "category": "family | work | hobby | routine | personal_history"
  }
  ```

### 2. Daily Routines (Günlük Rutinler) Segmenti
- **ID:** `[patient_id]-routine-[index]` (Örn: `P-1001-routine-0`)
- **Document:** `"[time] - [activity]. [description]"`
- **Metadata:**
  ```json
  {
    "patient_id": "P-XXXX",
    "type": "routine"
  }
  ```

## Sorgulama ve Filtreleme Stratejisi
Güvenlik ve doğruluk nedeniyle, yapılan tüm semantik sorgularda `patient_id` filtresi uygulanması zorunludur:
```python
results = collection.query(
    query_texts=["Sorgu metni"],
    where={"patient_id": "P-1001"}
)
```
