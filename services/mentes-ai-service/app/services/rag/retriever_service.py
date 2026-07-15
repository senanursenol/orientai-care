from db_config import chroma_collection

def retrieve_context(question, patient_id, category=None, n_results=2):
    """
    ChromaDB'den hasta bazlı semantik arama yapar.
    """

    where_filter = {
        "patient_id": patient_id
    }

    if category:
        where_filter = {
            "$and": [
                {"patient_id": patient_id},
                {"category": category}
            ]
        }

    results = chroma_collection.query(
        query_texts=[question],
        n_results=n_results,
        where=where_filter
    )

    return results