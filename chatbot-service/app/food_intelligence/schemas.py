from pydantic import BaseModel
from typing import List, Optional

class FoodAttributes(BaseModel):
    spice_level: Optional[str] = None  # mild | medium | hot

    contains_nuts: Optional[bool] = None
    contains_dairy: Optional[bool] = None
    gluten_free: Optional[bool] = None

    vegan: Optional[bool] = None
    vegetarian: Optional[bool] = None

    healthy_option: Optional[bool] = None
    kids_friendly: Optional[bool] = None

    popular_item: Optional[bool] = None
    cuisine_type: Optional[str] = None

    ingredients: List[str] = []
    dietary_tags: List[str] = []