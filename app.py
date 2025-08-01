from flask import Flask, request, render_template, jsonify
import os
import warnings
import re

# Suppress the specific FutureWarning from Torch
warnings.filterwarnings(
    "ignore",
    category=FutureWarning,
    message="`encoder_attention_mask` is deprecated and will be removed in version 4.55.0 for `BertSdpaSelfAttention.forward`."
)

from core.loader import load_pdf
from core.splitter import split_text
from core.vector_store import create_vector_store, get_all_document_ids
from core.rag_chain import create_rag_chain

app = Flask(__name__)

def sanitize_filename(filename):
    """Sanitizes a filename to be used as a document ID."""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', filename)

@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")

@app.route("/documents", methods=["GET"])
def list_documents():
    """Return a list of all ingested documents."""
    doc_ids = get_all_document_ids()
    return jsonify(doc_ids)

@app.route("/ingest", methods=["POST"])
def ingest():
    """Handle PDF file uploads and processing."""
    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return jsonify({"error": "No files selected"}), 400
    
    ingested_docs = []
    for file in files:
        if file and file.filename.endswith('.pdf'):
            if not os.path.exists("docs"):
                os.makedirs("docs")
            
            file_path = os.path.join("docs", file.filename)
            file.save(file_path)
            
            try:
                document_id = sanitize_filename(file.filename)
                pages = load_pdf(file.filename)
                chunks = split_text(pages)
                create_vector_store(document_id, chunks)
                ingested_docs.append(document_id)
            except Exception as e:
                return jsonify({"error": f"Error processing {file.filename}: {e}"}), 500
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            return jsonify({"error": f"Invalid file type: {file.filename}"}), 400

    return jsonify({
        "success": f"Successfully ingested {len(ingested_docs)} documents.",
        "ingested_documents": ingested_docs
    })

@app.route("/ask", methods=["POST"])
def ask():
    """Handle a user's question against a specific or all documents."""
    data = request.get_json()
    question = data.get("question")
    document_ids = data.get("document_ids", [])

    if not question:
        return jsonify({"error": "No question provided."}), 400
    
    if not document_ids:
        return jsonify({"error": "No documents selected."}), 400
        
    try:
        rag_chain = create_rag_chain(document_ids)
        result = rag_chain.invoke(question)
        
        serializable_sources = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in result.get("source_documents", [])
        ]
        
        return jsonify({
            "answer": result.get("answer", "No answer found."),
            "sources": serializable_sources,
            "followup_questions": result.get("followup_questions", [])
        })
    except Exception as e:
        print(f"Error in /ask endpoint for docs {document_ids}: {e}")
        return jsonify({"error": "An error occurred while processing your question."}), 500

if __name__ == "__main__":
    app.run(debug=True)