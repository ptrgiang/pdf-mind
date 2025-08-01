from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List

def split_text(text_pages: List[str]) -> List[Document]:
    """
    Splits a list of page texts into smaller chunks, preserving page number metadata.

    Args:
        text_pages: A list of strings, where each string is the text of a page.

    Returns:
        A list of Document objects, each with page_content and metadata.
    """
    # First, create Document objects for each page with its page number in metadata
    documents = [
        Document(page_content=page, metadata={"page_number": i + 1})
        for i, page in enumerate(text_pages)
    ]
    
    # Now, split these documents into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    
    chunks = text_splitter.split_documents(documents)
    
    return chunks