import os
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv


current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "..", ".env")
load_dotenv(dotenv_path=env_path)

# Veritabanı yolunu da ana dizine göre ayarlıyoruz
DB_PATH = os.getenv("CHROMA_DB_PATH", "../chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "patient_memories")

def init_chroma_db():
    """
    Belirtilen SentenceTransformer modeli ile ChromaDB'yi başlatır.
    """
    # Kullanılan SentenceTransformer modelini tanımla
    embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    
    #  Kalıcı veri klasörünü oluşturma
    client = chromadb.PersistentClient(path=DB_PATH)
    
   
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_function
    )
    
    return client, collection

# Uygulama genelinde kullanılmak üzere hazır nesneleri dışa aktar
chroma_client, chroma_collection = init_chroma_db()
