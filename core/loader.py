import fitz  # PyMuPDF
import os
from typing import List

def load_pdf(file_name: str) -> List[str]:
    """
    Loads a PDF file and extracts the text from each page.

    Args:
        file_name: The name of the PDF file in the 'docs' directory.

    Returns:
        A list of strings, where each string is the text content of a page.
    """
    docs_dir = "docs"
    file_path = os.path.join(docs_dir, file_name)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} was not found.")

    doc = fitz.open(file_path)
    pages_text = [page.get_text() for page in doc]
    doc.close()
    
    return pages_text

if __name__ == '__main__':
    # This is for testing the loader independently.
    # Create a dummy PDF in the 'docs' folder to test this.
    # For example, create a file named 'sample.pdf'.
    
    # Create a dummy file for testing
    if not os.path.exists("docs"):
        os.makedirs("docs")
    
    try:
        # Create a simple PDF for testing purposes
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), "This is a test document for the RAG project.")
        page.insert_text((50, 92), "It contains some text to be extracted.")
        doc.save("docs/sample.pdf")
        doc.close()

        print("Created 'docs/sample.pdf' for testing.")
        
        pages = load_pdf("sample.pdf")
        
        if pages:
            print(f"Successfully loaded 'sample.pdf'. It has {len(pages)} pages.")
            print("Content of the first page:")
            print(pages[0])
        else:
            print("Could not load the PDF or it is empty.")

    except Exception as e:
        print(f"An error occurred: {e}")

