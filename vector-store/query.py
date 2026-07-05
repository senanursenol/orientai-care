# 'services' klasörünün içindeki db_config'den çekiyoruz
from services.db_config import chroma_collection

patient_id = input("Hasta ID (Örn: P-1001): ").strip()
question = input("Sorunuzu girin: ").strip()

print("\nVeritabanında akıllı semantik arama yapılıyor...")

# 2. En benzer belgeyi arıyoruz
# Arka plandaki model soruyu otomatik olarak vektörleştiriyor.
results = chroma_collection.query(
    query_texts=[question],
    n_results=2,
    where={
        "$and": [
            {"patient_id": patient_id},
            {"category": "family"}
        ]
    }
)

print("\n Bulunan En Alakalı Sonuçlar:\n")

# Eğer sonuç bulunamazsa kontrolü
if not results["documents"] or not results["documents"][0]:
    print("Bu hastaya ait eşleşen bir bilgi bulunamadı.")
else:
    for document, metadata in zip(results["documents"][0], results["metadatas"][0]):
        print(f" Bilgi Tipi: {metadata.get('type', 'Bilinmiyor')}")
        if "category" in metadata:
            print(f" Kategori: {metadata['category']}")
        print(f" Belge İçeriği:\n{document}")
        print("-" * 40)
