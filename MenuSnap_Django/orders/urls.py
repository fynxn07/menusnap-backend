from django.urls import path

from .views import (
    AdminOrderDetailView,
    AdminOrdersView,
    KitchenOrdersView,
    WaiterOrdersView,
    OrderStatusView,
    TableOrderCreateView,
    UpdateOrderStatusView,
)

urlpatterns = [
    path("table/<uuid:table_id>/", TableOrderCreateView.as_view()),
    path("<int:order_id>/status/", OrderStatusView.as_view()),
    path("kitchen_order/", KitchenOrdersView.as_view()),
    path("waiter_order/", WaiterOrdersView.as_view()),
    path("kitchen/<int:order_id>/update_status/", UpdateOrderStatusView.as_view()),
    path("admin_order/", AdminOrdersView.as_view()),
    path("admin_order/<int:order_id>/", AdminOrderDetailView.as_view()),
]
