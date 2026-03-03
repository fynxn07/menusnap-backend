# # from langchain_community.vectorstores import Chroma
# # from langchain_community.embeddings import OllamaEmbeddings
# # from langchain_community.chat_models import ChatOllama
# # from langchain_text_splitters import RecursiveCharacterTextSplitter
# # from langchain.docstore.document import Document



# # def detect_food_filters(question: str) -> dict:
# #     """
# #     Detect dietary or preference intent from user question.
# #     Returns Chroma metadata filter dictionary.
# #     """

# #     q = question.lower()
# #     filters = {}

# #     # -------- Dietary --------
# #     if "vegetarian" in q or "veg" in q:
# #         filters["vegetarian"] = True

# #     if "vegan" in q:
# #         filters["vegan"] = True

# #     if "gluten free" in q:
# #         filters["gluten_free"] = True

# #     if "dairy free" in q:
# #         filters["contains_dairy"] = False

# #     if "nut free" in q or "no nuts" in q:
# #         filters["contains_nuts"] = False

# #     # -------- Spice --------
# #     if "not spicy" in q or "mild" in q:
# #         filters["spice_level"] = "mild"

# #     if "spicy" in q or "hot" in q:
# #         filters["spice_level"] = "hot"

# #     # -------- Preferences --------
# #     if "healthy" in q:
# #         filters["healthy_option"] = True

# #     if "kids" in q or "child" in q:
# #         filters["kids_friendly"] = True

# #     return filters


# # class RAGService:
# #     def __init__(self, restaurant_id: str):

# #         self.persist_dir = f"chroma_db/restaurant_{restaurant_id}"

# #         # ⭐ Use proper embedding model
# #         self.embeddings = OllamaEmbeddings(
# #             model="nomic-embed-text",
# #             base_url="http://ollama:11434"
# #         )

# #         self.vectorstore = Chroma(
# #             persist_directory=self.persist_dir,
# #             embedding_function=self.embeddings
# #         )

# #         self.llm = ChatOllama(
# #             model="phi3",
# #             base_url="http://ollama:11434",
# #             temperature=0.3,
# #             num_predict=200,   # limit output length
# #             keep_alive=400,
# #             num_ctx=2048,      # limit context window
# #             repeat_penalty=1.1
# #         )

# #     # ---------- INGEST ----------
# #     def ingest_text(self, text: str):

# #         splitter = RecursiveCharacterTextSplitter(
# #             chunk_size=500,
# #             chunk_overlap=50
# #         )

# #         docs = [Document(
# #             page_content=text,
# #             metadata={"source": "menu"}
# #         )]

# #         chunks = splitter.split_documents(docs)

# #         self.vectorstore.add_documents(chunks)
# #         self.vectorstore.persist()

# #     # ---------- ASK ----------
# #     def ask(self, question: str) -> str:

# #         filters = detect_food_filters(question)

# #         if filters:
# #             docs = self.vectorstore.similarity_search(
# #                 question,
# #                 k=2,
# #                 filter=filters
# #             )
# #         else:
# #             docs = self.vectorstore.similarity_search(
# #                 question,
# #                 k=2
# #             )

# #         if not docs:
# #             return "I don't have enough information about the menu yet."

# #         context = "\n".join([doc.page_content for doc in docs])
# #         context = context[:1500]  # safety limit


# #         prompt = f"""
# # You are a friendly AI assistant for a restaurant.

# # STRICT RULES :
# # - ONLY use dishes from Menu Context
# # - DO NOT invent dishes
# # - Recommend 2–4 relevant dishes
# # - Be polite and concise

# # Menu Context:
# # {context}

# # Customer Question:
# # {question}

# # """

# #         response = self.llm.invoke(prompt,timeout=60)
# #         return response.content


# from langchain_community.vectorstores import Chroma
# from langchain_community.embeddings import OllamaEmbeddings
# from langchain_community.chat_models import ChatOllama


# class RAGService:
#     """
#     Production-optimized RAG service for MenuSnap
#     """

#     def __init__(self, restaurant_id: str):

#         self.restaurant_id = restaurant_id
#         self.persist_dir = f"chroma_db/restaurant_{restaurant_id}"

#         # ---------- EMBEDDINGS (LOAD ONCE) ----------
#         self.embeddings = OllamaEmbeddings(
#             model="nomic-embed-text",
#             base_url="http://ollama:11434"
#         )

#         # ---------- VECTOR STORE (LOAD ONCE) ----------
#         self.vectorstore = Chroma(
#             persist_directory=self.persist_dir,
#             embedding_function=self.embeddings
#         )

#         # ---------- LLM CLIENT (KEEP HOT) ----------
#         self.llm = ChatOllama(
#             model="phi3",
#             base_url="http://ollama:11434",
#             temperature=0.3,
#             num_predict=150,      # shorter responses = faster
#             keep_alive=600,       # keep model in memory
#             num_ctx=1024,         # smaller context = faster
#             repeat_penalty=1.1,
#         )

#     # -------------------------------------------------
#     # ⚡ RULE-BASED FAST PATH (NO LLM)
#     # -------------------------------------------------
#     def fast_path(self, question: str):

#         q = question.lower()

#         if "menu" in q:
#             return "Please use the QR menu to browse all available dishes."

#         if "open" in q or "hours" in q or "timing" in q:
#             return "We are open from 10 AM to 10 PM daily."

#         if "location" in q or "address" in q:
#             return "You can find our location on Google Maps."

#         if "contact" in q or "phone" in q:
#             return "Please contact the restaurant directly for assistance."

#         return None

#     # -------------------------------------------------
#     # 🧠 MAIN CHAT FUNCTION
#     # -------------------------------------------------
#     def ask(self, question: str) -> str:

#         # 🚀 FAST PATH FIRST
#         fast_answer = self.fast_path(question)
#         if fast_answer:
#             return fast_answer

#         # ---------- VECTOR SEARCH ----------
#         docs = self.vectorstore.similarity_search(
#             question,
#             k=3  # small = fast
#         )

#         if not docs:
#             return "I don't have enough information about the menu yet."

#         context = "\n".join(doc.page_content for doc in docs)

#         # Safety trim
#         context = context[:1200]

#         # ---------- PROMPT ----------
#         prompt = f"""
# You are a helpful AI assistant for a restaurant.

# IMPORTANT RULES:
# - Use ONLY dishes from the menu context
# - Do NOT invent items
# - Recommend 2–4 relevant dishes
# - Be polite and concise

# Menu Context:
# {context}

# Customer Question:
# {question}

# Answer:
# """

#         # ---------- LLM CALL ----------
#         response = self.llm.invoke(prompt)

#         return response.content.strip()


from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama



class RAGService:
    """
    Production-optimized RAG service for MenuSnap
    """

    def __init__(self, restaurant_id: str):
        
        import os


        self.restaurant_id = restaurant_id
        self.persist_dir = f"chroma_db/restaurant_{restaurant_id}"
        
        os.makedirs(self.persist_dir,exist_ok=True)

        # ---------- EMBEDDINGS (LOAD ONCE) ----------
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://ollama:11434"
        )

        # ---------- VECTOR STORE (LOAD ONCE) ----------
        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings
        )

        # ---------- LLM CLIENT (KEEP HOT) ----------
        self.llm = ChatOllama(
            model="phi3",
            base_url="http://ollama:11434",
            temperature=0.2,
            num_predict=80,      # shorter responses = faster
            keep_alive=600,       # keep model in memory
            num_ctx=768,         # smaller context = faster
            repeat_penalty=1.1,
        )

    # -------------------------------------------------
    # ⚡ RULE-BASED FAST PATH (NO LLM)
    # -------------------------------------------------
    def fast_path(self, question: str):

        q = question.lower()

        if "menu" in q:
            return "Please use the QR menu to browse all available dishes."

        if "open" in q or "hours" in q or "timing" in q:
            return "We are open from 10 AM to 10 PM daily."

        if "location" in q or "address" in q:
            return "You can find our location on Google Maps."

        if "contact" in q or "phone" in q:
            return "Please contact the restaurant directly for assistance."

        return None

    # -------------------------------------------------
    # 🧠 MAIN CHAT FUNCTION
    # -------------------------------------------------
    def ask(self, question: str) -> str:

        # 🚀 FAST PATH FIRST
        fast_answer = self.fast_path(question)
        if fast_answer:
            return fast_answer

        # ---------- VECTOR SEARCH ----------
        docs = self.vectorstore.similarity_search(
            question,
            k=3  # small = fast
        )

        if not docs:
            return "I don't have enough information about the menu yet."
        
        
        items=[]

        for d in docs:
            for line in d.page_content.split("\n"):
                if line.lower().startswith("dish:"):
                    items.append(line.replace("Dish:", "").strip())

        if items:
            return "Here are some recommendations:\n" + "\n".join(
                f"• {i}" for i in items[:4]
            )

        context = "\n".join(doc.page_content for doc in docs)[:1000]

        # ---------- PROMPT ----------
        prompt = f"""
You are a helpful AI assistant for a restaurant.

IMPORTANT RULES:
- Use ONLY dishes from the menu context
- Do NOT invent items
- Recommend 2–4 relevant dishes
- Be polite and concise

Menu Context:
{context}

Customer Question:
{question}

Answer:
"""

        # ---------- LLM CALL ----------
        response = self.llm.invoke(prompt)

        return response.content.strip()