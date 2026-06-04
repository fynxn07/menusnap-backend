import httpx

from app.models.menu import MenuItemDoc
from app.services.rag.rag_service import RAGService
from app.food_intelligence.document_builder import build_menu_document


BACKEND_URL = "http://backend:8000"


# ============================================
# FETCH MENU FROM DJANGO
# ============================================

async def fetch_menu_from_backend(
    restaurant_id: int,
    token: str
):

    url = f"{BACKEND_URL}/menu/export/{restaurant_id}/"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    async with httpx.AsyncClient(timeout=60) as client:

        response = await client.get(
            url,
            headers=headers
        )

        response.raise_for_status()

        return response.json()


# ============================================
# TRANSFORM RAW ITEMS
# ============================================

def transform_to_ai_docs(raw_items):

    docs = []

    for item in raw_items:

        doc = MenuItemDoc(
            restaurant_id=str(item["restaurant_id"]),
            item_id=str(item["id"]),
            name=item["name"],
            category=item.get("category_name"),
            description=item.get("description"),
            price=float(item["price"]) if item.get("price") else None,
            vegetarian=item.get("is_veg"),
        )

        docs.append(doc)

    return docs


# ============================================
# INGEST INTO VECTOR STORE
# ============================================

def ingest_to_vectorstore(docs):

    if not docs:
        return

    restaurant_id = docs[0].restaurant_id

    from app.api.routes.chat import get_rag

    rag = get_rag(restaurant_id)

    documents = []

    for doc in docs:

        dish_dict = {
            "id": doc.item_id,
            "name": doc.name,
            "category": doc.category,
            "description": doc.description,
            "price": doc.price,
            "ingredients": (
                doc.ingredients
                if hasattr(doc, "ingredients")
                else []
            ),
        }

        ai_doc = build_menu_document(
            dish=dish_dict,
            restaurant_id=restaurant_id
        )

        documents.append(ai_doc)

    # ====================================
    # ADD TO CHROMA
    # ====================================

    rag.vectorstore.add_documents(documents)