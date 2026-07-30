from app.services.rag.retriever_service import retrieve_context
from app.services.rag.prompt_builder import build_image_memory_prompt


def _build_search_query(image_description, detected_labels=None):
    """Vision çıktısını (açıklama + varsa etiketler) tek bir arama sorgusuna çevirir."""
    if not detected_labels:
        return image_description
    return f"{image_description} ({', '.join(detected_labels)})"


def retrieve_memories_for_image(
    image_description,
    patient_id,
    detected_labels=None,
    n_results=3,
):
    """
    Vision servisinden gelen fotoğraf açıklamasını hastanın kişisel anı/rutin
    hafızasıyla (ChromaDB, patient_id filtreli) ilişkilendirir.

    Dönüş: { context: str, documents: list, has_context: bool, prompt: str }
    """
    query = _build_search_query(image_description, detected_labels)

    results = retrieve_context(
        question=query,
        patient_id=patient_id,
        n_results=n_results,
    )

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    found_documents = documents[0] if documents else []
    found_metadatas = metadatas[0] if metadatas else []

    has_context = bool(found_documents)
    context = "\n".join(found_documents) if has_context else ""

    prompt = build_image_memory_prompt(
        context=context if has_context else "Bu görsel için hastaya ait ilgili bir anı veya rutin bulunamadı.",
        image_description=image_description,
        question=query,
    )

    return {
        "context": context,
        "documents": [
            {"content": doc, "metadata": meta}
            for doc, meta in zip(found_documents, found_metadatas)
        ],
        "has_context": has_context,
        "prompt": prompt,
    }
