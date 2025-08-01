import os
import shutil
from typing import List
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

# Define the base path for storing all vector stores
VECTOR_STORES_BASE_PATH = "vector_stores"

def get_vector_store_path(document_id: str) -> str:
    """Constructs the path for a specific document's vector store."""
    return os.path.join(VECTOR_STORES_BASE_PATH, document_id)

def create_vector_store(document_id: str, chunks: List[Document]):
    """
    Creates and saves a FAISS vector store for a specific document.
    """
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store_path = get_vector_store_path(document_id)

    # If a store already exists, remove it to ensure a fresh start
    if os.path.exists(vector_store_path):
        shutil.rmtree(vector_store_path)
    
    print(f"Creating vector store for document: {document_id}")
    vector_store = FAISS.from_documents(chunks, embedding=embeddings)
    vector_store.save_local(vector_store_path)
    print(f"Vector store saved to {vector_store_path}")

def load_vector_store(document_id: str) -> FAISS:
    """
    Loads an existing FAISS vector store for a specific document.
    """
    vector_store_path = get_vector_store_path(document_id)
    
    if not os.path.exists(vector_store_path):
        raise FileNotFoundError(f"Vector store for document {document_id} not found.")

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    return FAISS.load_local(
        vector_store_path, 
        embeddings, 
        allow_dangerous_deserialization=True
    )

def get_all_document_ids() -> List[str]:
    """
    Returns a list of all document IDs that have a vector store.
    """
    if not os.path.exists(VECTOR_STORES_BASE_PATH):
        return []
    return [name for name in os.listdir(VECTOR_STORES_BASE_PATH) if os.path.isdir(os.path.join(VECTOR_STORES_BASE_PATH, name))]
