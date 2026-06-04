import os
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings

# ============================================
# CONFIGURE GEMINI
# ============================================

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


# ============================================
# RAG SERVICE
# ============================================

class RAGService:

    def __init__(self, restaurant_id: str):

        self.restaurant_id = restaurant_id

        # ====================================
        # GEMINI EMBEDDINGS
        # ====================================

        self.embedding = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=settings.GEMINI_API_KEY
        )

        # ====================================
        # CHROMA DB
        # ====================================

        self.persist_directory = f"chroma_db/{restaurant_id}"

        self.vectorstore = Chroma(
            collection_name=f"restaurant_{restaurant_id}",
            persist_directory=self.persist_directory,
            embedding_function=self.embedding
        )

        # ====================================
        # TEXT SPLITTER
        # ====================================

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )

        # ====================================
        # GEMINI MODEL WITH SYSTEM INSTRUCTION
        # ====================================

        self.model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL_NAME,
            system_instruction=(
                "You are MenuSnap AI Assistant for restaurants. "
                "Your goal is to provide fast, accurate information about the menu. "
                "Always be polite, concise, and helpful. "
                "Base your answers EXCLUSIVELY on the provided menu context. "
                "If the information is not in the menu, politely say you don't know. "
                "Recommend popular or specific items when relevant to the user's question."
            )
        )

    # ============================================
    # INGEST TEXT
    # ============================================

    def ingest_text(self, text: str):

        chunks = self.splitter.split_text(text)

        docs = [
            Document(
                page_content=chunk,
                metadata={
                    "restaurant_id": self.restaurant_id
                }
            )
            for chunk in chunks
        ]

        self.vectorstore.add_documents(docs)

    # ============================================
    # ASK QUESTION
    # ============================================

    def ask(self, question: str):

        try:

            # ====================================
            # SEARCH VECTOR DB
            # ====================================

            docs = self.vectorstore.similarity_search(
                question,
                k=2
            )

            if not docs:
                return "Sorry, I couldn't find anything in the menu."

            # ====================================
            # BUILD CONTEXT
            # ====================================

            context = "\n\n".join([
                doc.page_content
                for doc in docs
            ])

            # ====================================
            # PROMPT
            # ====================================

            prompt = f"Menu Context:\n{context}\n\nCustomer Question: {question}"

            # ====================================
            # GEMINI RESPONSE
            # ====================================

            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "max_output_tokens": 300,
                }
            )

            if not response.text:
                return "Sorry, I couldn't generate a response."

            return response.text

        except Exception as e:

            print(f"[Gemini Error] {e}")

            return "AI service temporarily unavailable."