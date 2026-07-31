from services.retriever_service import retrieve_context
from services.log_service import save_interaction
patient_id = input("Hasta ID (Örn: P-1001): ").strip()
question = input("Sorunuzu girin: ").strip()

print("\nVeritabanında akıllı semantik arama yapılıyor...")

# 2. En benzer belgeyi arıyoruz
# Arka plandaki model soruyu otomatik olarak vektörleştiriyor.
results = retrieve_context(
    question=question,
    patient_id=patient_id,
)
print("\n Bulunan En Alakalı Sonuçlar:\n")

# Eğer sonuç bulunamazsa kontrolü
if not results["documents"] or not results["documents"][0]:
    print("Bu hastaya ait eşleşen bir bilgi bulunamadı.")
else:
    response = ""

    for document, metadata in zip(results["documents"][0], results["metadatas"][0]):
        print(f" Bilgi Tipi: {metadata.get('type', 'Bilinmiyor')}")
        if "category" in metadata:
            print(f" Kategori: {metadata['category']}")
        print(f" Belge İçeriği:\n{document}")
        print("-" * 40)

        response += document + "\n"

    save_interaction(
        patient_id=1,
        user_input=question,
        response=response,
        input_type="text"
    )
