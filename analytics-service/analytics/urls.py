from .views import RestaurantEventsView,RevenueView,PeakHoursView,PopularDishesView,OrderTrendsView,TableUtilizationView
from django.urls import path


urlpatterns=[
    path("restaurants/<str:restaurant_id>/events/",RestaurantEventsView.as_view()),
    path("restaurants/<str:restaurant_id>/revenue/",RevenueView.as_view()),
    path("restaurants/<str:restaurant_id>/peak-hours/",PeakHoursView.as_view()),
    path("restaurants/<str:restaurant_id>/order-trends/",OrderTrendsView.as_view()),
    path("restaurants/<str:restaurant_id>/popular-dishes/",PopularDishesView.as_view()),
    path("restaurants/<str:restaurant_id>/table-utilization/",TableUtilizationView.as_view()),
    
]

