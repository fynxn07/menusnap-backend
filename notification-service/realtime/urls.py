from django.urls import path
from .views import NotifyKitchenView,NotifyWaiterView

urlpatterns = [
    path("notify_kitchen/", NotifyKitchenView.as_view()),
    path("notify_waiter/",NotifyWaiterView.as_view()),
]