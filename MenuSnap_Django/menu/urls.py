from cloudinary.models import CloudinaryField
from django.urls import path

from .views import (
    CustomerMenuView,
    MenuCategoryDetailView,
    MenuCategoryListCreateView,
    MenuItemDetailView,
    MenuItemListCreateView,
    MenuStatsView,
    PublicMenuView,
    MenuExportView,
)

urlpatterns = [
    path("categories/", MenuCategoryListCreateView.as_view()),
    path("categories/<int:pk>/", MenuCategoryDetailView.as_view()),
    path("items/", MenuItemListCreateView.as_view()),
    path("items/<int:pk>/", MenuItemDetailView.as_view()),
    path("stats/", MenuStatsView.as_view()),
    path(
        "customer_menu/<int:restaurant_id>/<uuid:table_id>/", CustomerMenuView.as_view()
    ),
    path("public_menu/<int:restaurant_id>/", PublicMenuView.as_view()),
    path("export/<int:restaurant_id>/",MenuExportView.as_view()),
]
