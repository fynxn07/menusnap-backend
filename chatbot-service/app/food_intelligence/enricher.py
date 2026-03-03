from typing import Dict, Any

from app.food_intelligence.rules import infer_attributes_rule_based
from app.food_intelligence.schemas import FoodAttributes


def build_food_attributes(dish: Dict[str, Any]) -> FoodAttributes:
    """
    Build structured attributes for a dish using rule-based inference.
    dish = raw menu item dict from backend
    """

    text_parts = [
        dish.get("name", ""),
        dish.get("description", ""),
        " ".join(dish.get("ingredients", [])),
    ]

    full_text = " ".join(text_parts)

    attrs_dict = infer_attributes_rule_based(full_text)

    # Include ingredients if provided
    attrs_dict["ingredients"] = dish.get("ingredients", [])

    return FoodAttributes(**attrs_dict)