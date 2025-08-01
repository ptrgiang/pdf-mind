# PDF Mind: Chat with Your Documents

PDF Mind is a web-based application that allows you to upload your PDF documents and have a conversation with them. Using a Retrieval-Augmented Generation (RAG) pipeline, this tool enables you to ask questions about your documents and get answers based on their content.

## Features

- **PDF Upload:** Upload one or more PDF documents for processing.
- **Document Library:** View a list of all ingested documents.
- **Multi-Document Chat:** Select one or more documents to chat with simultaneously.
- **Content-Based Answering:** Get answers to your questions based on the content of the selected documents.
- **Source Highlighting:** See the exact source text from which the answer was generated.
- **Follow-up Questions:** Get suggestions for relevant follow-up questions.

## Technical Stack

- **Backend:** Flask
- **Frontend:** HTML, CSS, JavaScript
- **Core AI/RAG:**
  - LangChain
  - Google Generative AI (Gemini)
  - HuggingFace Sentence Transformers (for embeddings)
  - FAISS (for vector storage)
  - PyMuPDF (for PDF text extraction)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd pdf-mind
    ```

2.  **Create a virtual environment and activate it:**
    First, create the virtual environment:
    ```bash
    python -m venv .venv
    ```
    Then, activate it using the command for your shell:
    - **Windows (Command Prompt):** `.venv\Scripts\activate`
    - **Windows (PowerShell):** `.venv\Scripts\Activate.ps1`
    - **macOS/Linux:** `source .venv/bin/activate`

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file:**
    Create a `.env` file in the root directory and add your Google API key:
    ```
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
    ```

## Usage

1.  **Run the Flask application:**
    With the virtual environment activated, run the app using one of the following commands. Using `python -m flask run` is generally more reliable.
    ```bash
    python -m flask run
    ```
    Alternatively, you can directly run the main script:
    ```bash
    python app.py
    ```

2.  **Open your browser:**
    Navigate to `http://127.0.0.1:5000`.

3.  **Upload Documents:**
    - Click on "Choose PDFs" to select one or more PDF files.
    - Click "Upload & Ingest" to process and store the documents.

4.  **Chat with Documents:**
    - Select the document(s) you want to chat with from the "Document Library".
    - The chat interface will appear.
    - Type your question in the input box and press Enter.

## How It Works

1.  **Ingestion:** When a PDF is uploaded, the text is extracted from each page.
2.  **Chunking:** The extracted text is split into smaller, overlapping chunks.
3.  **Embedding & Storage:** Each chunk is converted into a vector embedding and stored in a FAISS vector store. A separate vector store is created for each document.
4.  **Retrieval:** When you ask a question, the application retrieves the most relevant chunks from the selected documents' vector stores.
5.  **Re-ranking:** A cross-encoder re-ranks the retrieved chunks for better relevance.
6.  **Generation:** The top-ranked chunks are passed to a Gemini model along with your question to generate a comprehensive answer.
