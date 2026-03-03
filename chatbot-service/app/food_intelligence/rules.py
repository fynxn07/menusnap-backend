from typing import Dict


# ---------- Keyword Dictionaries ----------

SPICY_WORDS = [
    "spicy", "chilli", "chili", "pepper", "masala", "hot"
]

NUT_WORDS = [
    "peanut", "cashew", "almond", "pistachio", "nut"
]

DAIRY_WORDS = [
    "cheese", "milk", "cream", "butter", "paneer", "ghee", "yogurt"
]

GLUTEN_WORDS = [
    "wheat", "maida", "bread", "pasta", "noodle", "flour"
]

MEAT_WORDS = [
    "chicken", "mutton", "beef", "fish", "prawn", "egg", "lamb"
]

HEALTHY_WORDS = [
    "grilled", "steamed", "salad", "low fat", "baked"
]

KID_WORDS = [
    "sweet", "mild", "cheese", "chocolate", "cream"
]


# ---------- Core Inference Function ----------

def infer_attributes_rule_based(text: str) -> Dict:
    """
    Infer food attributes from dish text using rules only.
    Works offline and deterministic.
    """

    t = text.lower()

    attrs = {
        "spice_level": None,
        "contains_nuts": any(w in t for w in NUT_WORDS),
        "contains_dairy": any(w in t for w in DAIRY_WORDS),
        "gluten_free": not any(w in t for w in GLUTEN_WORDS),
        "vegetarian": not any(w in t for w in MEAT_WORDS),
        "vegan": (
            not any(w in t for w in MEAT_WORDS)
            and not any(w in t for w in DAIRY_WORDS)
        ),
        "healthy_option": any(w in t for w in HEALTHY_WORDS),
        "kids_friendly": any(w in t for w in KID_WORDS),
    }

    # ----- Spice Level -----
    if any(w in t for w in SPICY_WORDS):
        attrs["spice_level"] = "hot"
    else:
        attrs["spice_level"] = "mild"

    return attrs