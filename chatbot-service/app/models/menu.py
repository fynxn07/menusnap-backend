from pydantic import BaseModel, Field
from typing import List, Optional


class MenuItemDoc(BaseModel):
    # -------- Core Identity --------
    restaurant_id: str
    item_id: str

    # -------- Basic Info --------
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

    # -------- Dietary Info --------
    vegetarian: Optional[bool] = None
    vegan: Optional[bool] = None
    spicy_level: Optional[str] = None  # mild / medium / hot

    contains_nuts: Optional[bool] = None
    contains_dairy: Optional[bool] = None
    gluten_free: Optional[bool] = None

    # -------- Ingredients & Tags --------
    ingredients: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


