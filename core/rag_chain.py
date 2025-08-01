from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough, RunnableMap, RunnableLambda
from langchain.schema.output_parser import StrOutputParser
from sentence_transformers.cross_encoder import CrossEncoder
import numpy as np
import re
from typing import List

from core.vector_store import load_vector_store, get_all_document_ids

# Load environment variables from .env file
load_dotenv()

class CustomOutputParser(StrOutputParser):
    """
    Parses the LLM output to separate the answer from follow-up questions.
    """
    def parse(self, text: str) -> dict:
        # Find the follow-up questions section
        follow_up_match = re.search(r"---FOLLOW_UP_QUESTIONS---(.*)", text, re.DOTALL)
        
        if follow_up_match:
            answer = text[:follow_up_match.start()].strip()
            questions_str = follow_up_match.group(1).strip()
            follow_up_questions = [q.strip() for q in questions_str.split('\n') if q.strip()]
        else:
            answer = text.strip()
            follow_up_questions = []
            
        return {
            "answer": answer,
            "followup_questions": follow_up_questions
        }

def format_docs(docs):
    """Helper function to format docs for the prompt."""
    return "\n\n".join(
        f"Source: {doc.metadata.get('source', 'N/A')}, Page: {doc.metadata.get('page_number', 'N/A')}\nContent: {doc.page_content}"
        for doc in docs
    )

def create_rag_chain(document_ids: List[str]):
    """
    Creates a RAG chain for question-answering across a list of specified document IDs.
    """
    # --- Retriever Setup ---
    if not document_ids:
        def dummy_chain(_):
            return {"answer": "Please select at least one document to chat with.", "source_documents": [], "followup_questions": []}
        return RunnableLambda(dummy_chain)

    all_retrievers = []
    for doc_id in document_ids:
        try:
            vector_store = load_vector_store(doc_id)
            retriever = vector_store.as_retriever(search_kwargs={'k': 10})
            
            def add_source_metadata(docs, doc_id=doc_id):
                for doc in docs:
                    doc.metadata['source'] = doc_id
                return docs
            
            all_retrievers.append(retriever | add_source_metadata)
        except FileNotFoundError:
            print(f"Warning: Vector store for document {doc_id} not found. Skipping.")
            continue

    if not all_retrievers:
        def dummy_chain(_):
            return {"answer": "Could not find any valid documents to search.", "source_documents": [], "followup_questions": []}
        return RunnableLambda(dummy_chain)

    def combined_retriever(query):
        all_retrieved = []
        for retriever_chain in all_retrievers:
            all_retrieved.extend(retriever_chain.invoke(query))
        
        if not all_retrieved:
            return []

        cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        pairs = [[query, doc.page_content] for doc in all_retrieved]
        scores = cross_encoder.predict(pairs)
        
        scored_docs = sorted(zip(scores, all_retrieved), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:5]]

    retriever = RunnableLambda(combined_retriever)

    # --- LLM and Prompt Setup ---
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
    template = """
    You are a helpful assistant. Your task is to answer the user's question based only on the provided context.
    After providing a comprehensive answer, you must suggest 3 relevant follow-up questions that the user might want to ask next.

    **Instructions:**
    1.  First, provide a clear and detailed answer to the question.
    2.  Cite your sources at the end of each sentence that uses information from the context, like this: [Source: filename.pdf, Page: 12].
    3.  If the context does not contain the answer, state that you don't know.
    4.  After the answer, add a separator line: ---FOLLOW_UP_QUESTIONS---
    5.  Below the separator, list exactly 3 distinct and insightful follow-up questions. Do not add any preamble.

    **Context:**
    {context}

    **Question:**
    {question}

    **Answer and Follow-up Questions:**
    """
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])

    # --- RAG Chain Assembly ---
    rag_chain_from_docs = (
        {
            "context": lambda x: format_docs(x["documents"]),
            "question": lambda x: x["question"],
        }
        | prompt
        | llm
        | CustomOutputParser()
    )

    rag_chain_with_source = RunnableMap(
        {
            "documents": retriever,
            "question": RunnablePassthrough(),
        }
    ) | {
        "source_documents": lambda x: x["documents"],
        "answer": lambda x: rag_chain_from_docs.invoke(x)["answer"],
        "followup_questions": lambda x: rag_chain_from_docs.invoke(x)["followup_questions"],
    }
    
    return rag_chain_with_source
