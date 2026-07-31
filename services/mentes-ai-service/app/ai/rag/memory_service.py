from services.retriever_service import retrieve_context


def retrieve_memories(patient_id, vision_result):
    """
    Vision modelinden gelen kişi, nesne ve bağlam bilgisini kullanarak
    ilgili anıları ChromaDB'de arar.

    Tüm alanlar aranır ve sonuçlar birleştirilir.
    Tekrar eden anılar kaldırılır.
    """

    search_queries = [
        vision_result.get("person"),
        vision_result.get("object"),
        vision_result.get("context"),
    ]

    # None veya boş olanları çıkar
    search_queries = [q for q in search_queries if q]

    all_memories = []

    for query in search_queries:

        results = retrieve_context(
            question=query,
            patient_id=patient_id,
        )

        if results["documents"] and results["documents"][0]:

            for document in results["documents"][0]:

                if document not in all_memories:
                    all_memories.append(document)

    if not all_memories:
        return None

    return all_memories

def generate_memory_response(memories):

    if not memories:
        return (
            "Üzgünüm, bu fotoğrafla ilgili kayıtlı bir anı bulamadım. "
            "Yanlış bilgi vermek istemem."
        )

    response = (
        "Bu fotoğraf size tanıdık gelebilir. "
        "Kayıtlarınıza göre şunları hatırlıyorum:\n\n"
    )

    # En fazla 3 anı göster
    for memory in memories[:3]:

        clean_memory = memory

        if "Memory:" in clean_memory:
            clean_memory = clean_memory.split("Memory:", 1)[1].strip()

        response += f"• {clean_memory}\n"

    response += (
        "\nUmarım bu bilgiler size yardımcı olur. "
        "İsterseniz birlikte bu kişi hakkında konuşabiliriz."
    )

    return response