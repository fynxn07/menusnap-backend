from django.urls import path

from .views import (
    BulkTableCreateView,
    CompleteOnboardingView,
    RestaurantBrandingView,
    RestaurantLogoUploadView,
    RestaurantOnboardingView,
    JoinTableView,
    RestaurantTablesView,
)

urlpatterns = [
    path("onboarding_details/", RestaurantOnboardingView.as_view()),
    path("onboarding_branding/", RestaurantBrandingView.as_view()),
    path("tables_create/", BulkTableCreateView.as_view()),
    path("complete_onboarding/", CompleteOnboardingView.as_view()),
    path("upload_logo/", RestaurantLogoUploadView.as_view()),
    path("join-table/", JoinTableView.as_view(), name="join-table"),
    path("tables/", RestaurantTablesView.as_view()),
    
]
