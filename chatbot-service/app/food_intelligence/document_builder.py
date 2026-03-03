from typing import Dict, Any

from langchain.schema import Document

from app.food_intelligence.enricher import build_food_attributes


def build_menu_document(
    dish: Dict[str, Any],
    restaurant_id: str,
) -> Document:
    """
    Convert a menu item into an AI-ready LangChain Document
    with structured metadata for Chroma.
    """

    attrs = build_food_attributes(dish)

    # -------- Text content for semantic search --------
    content = f"""
Dish: {dish.get("name", "")}
Category: {dish.get("category", "")}
Description: {dish.get("description", "")}
Ingredients: {", ".join(attrs.ingredients)}
Price: {dish.get("price", "")}
"""

    # -------- Metadata for filtering --------
    metadata = {
        "restaurant_id": restaurant_id,
        "item_id": dish.get("id"),

        "spice_level": attrs.spice_level,
        "contains_nuts": attrs.contains_nuts,
        "contains_dairy": attrs.contains_dairy,
        "gluten_free": attrs.gluten_free,
        "vegan": attrs.vegan,
        "vegetarian": attrs.vegetarian,
        "healthy_option": attrs.healthy_option,
        "kids_friendly": attrs.kids_friendly,
        "popular_item": attrs.popular_item,
        "cuisine_type": attrs.cuisine_type,
    }

    # ✅ Add optional lists ONLY if non-empty
    if attrs.ingredients:
        metadata["ingredients"] = attrs.ingredients

    if attrs.dietary_tags:
        metadata["dietary_tags"] = attrs.dietary_tags

    return Document(page_content=content.strip(), metadata=metadata)