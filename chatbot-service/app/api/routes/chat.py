from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
import threading
import os
import shutil

from langchain_community.document_loaders import PyPDFLoader

from app.services.rag.rag_service import RAGService
from app.services.rag.menu_sync_service import (
    fetch_menu_from_backend,
    transform_to_ai_docs,
    ingest_to_vectorstore,
)

from analytics_pipeline.producers.python.analytics_producer import AnalyticsProducer


router = APIRouter()

# =================================================
# 🔥 GLOBAL RAG CACHE (PER RESTAURANT)
# =================================================
RAG_INSTANCES = {}


def get_rag(restaurant_id: str) -> RAGService:
    if restaurant_id not in RAG_INSTANCES:
        RAG_INSTANCES[restaurant_id] = RAGService(restaurant_id)
    return RAG_INSTANCES[restaurant_id]


# =================================================
# 📦 REQUEST MODELS
# =================================================
class IngestRequest(BaseModel):
    restaurant_id: str
    text: str


class QueryRequest(BaseModel):
    restaurant_id: str
    question: str


class MenuSyncRequest(BaseModel):
    restaurant_id: int
    token: str


# =================================================
# ❤️ HEALTH CHECK
# =================================================
@router.get("/health")
def health_check():
    return {
        "service": "chatbot-service",
        "status": "healthy"
    }


# =================================================
# 📥 MANUAL TEXT INGEST
# =================================================
@router.post("/ingest")
def ingest_data(data: IngestRequest):

    rag = get_rag(data.restaurant_id)
    rag.ingest_text(data.text)

    return {"message": "Data ingested successfully"}


# =================================================
# 💬 CHAT ENDPOINT (FAST + PRODUCTION SAFE)
# =================================================
@router.post("/ask")
def ask_question(data: QueryRequest):

    # ---------- NON-BLOCKING ANALYTICS ----------
    def send_analytics():
        try:
            producer = AnalyticsProducer()

            producer.send_event(
                event_type="chatbot_question",
                restaurant_id=str(data.restaurant_id),
                source="chatbot",
                data={"question": data.question},
            )
        except Exception as e:
            print(f"[Analytics] chatbot_question failed: {e}")

    threading.Thread(target=send_analytics, daemon=True).start()

    # ---------- GET CACHED RAG ----------
    rag = get_rag(data.restaurant_id)

    # ---------- AI RESPONSE ----------
    answer = rag.ask(data.question)

    return {"answer": answer}


# =================================================
# 📁 FILE UPLOAD INGESTION
# =================================================
@router.post("/upload")
def upload_file(
    restaurant_id: str = Form(...),
    file: UploadFile = File(...)
):
    folder = f"uploads/restaurant_{restaurant_id}"
    os.makedirs(folder, exist_ok=True)

    file_path = f"{folder}/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rag = get_rag(restaurant_id)

    # ---------- PDF ----------
    if file.content_type == "application/pdf":
        loader = PyPDFLoader(file_path)
        pages = loader.load()

        for page in pages:
            rag.ingest_text(page.page_content)

    # ---------- TXT ----------
    elif file.filename.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            rag.ingest_text(f.read())

    else:
        return {"error": "Unsupported file type"}

    return {"message": "File uploaded and ingested successfully"}


# =================================================
# 🔄 MENU SYNC FROM DJANGO BACKEND
# =================================================
@router.post("/menu-sync")
async def menu_sync(data: MenuSyncRequest):

    try:
        raw_items = await fetch_menu_from_backend(
            data.restaurant_id,
            data.token
        )

        if not raw_items:
            return {"error": "Backend returned empty menu"}

        docs = transform_to_ai_docs(raw_items)

        # Ensure string ID consistency
        for d in docs:
            d.restaurant_id = str(data.restaurant_id)

        ingest_to_vectorstore(docs)

        return {
            "message": "Menu synced successfully",
            "items_indexed": len(docs)
        }

    except Exception as e:
        return {"error": str(e)}