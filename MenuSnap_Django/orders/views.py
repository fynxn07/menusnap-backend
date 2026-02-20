from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from menu.models import MenuItem
from restaurants.models import Table

from .models import Order, OrderItem
from .serializers import (
    AdminOrderDetailSerializer,
    AdminOrderListSerializer,
    KitchenOrdersResponseSerializer,
    OrderStatusSerializer,
    TableOrderCreateResponseSerializer,
    TableOrderCreateSerializer,
    UpdateOrderStatusResponseSerializer,
)

# Create your views here.


class TableOrderCreateView(APIView):
    permission_classes = []

    @transaction.atomic
    def post(self, request, table_id):
        serializer = TableOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        table = Table.objects.select_related("restaurant").filter(id=table_id).first()
        if not table:
            return Response(
                {"detail": "Invalid table"}, status=status.HTTP_404_NOT_FOUND
            )

        restaurant = table.restaurant
        total = 0
        order_items = []
        order_items_data = []

        for item in serializer.validated_data["items"]:

            menu_item = MenuItem.objects.filter(
                id=item["menu_item"],
                restaurant=restaurant,
                is_active=True,
                is_available=True,
            ).first()

            if not menu_item:
                return Response(
                    {"detail": f"Invalid menu item {item['menu_item']}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            qty = item["quantity"]
            total += menu_item.price * qty

            order_items.append(
                OrderItem(menu_item=menu_item, quantity=qty, price=menu_item.price)
            )

            order_items_data.append(
                {
                    "id": len(order_items_data) + 1,
                    "quantity": qty,
                    "menu_item": {
                        "id": menu_item.id,
                        "name": menu_item.name,
                        "price": str(menu_item.price),
                    },
                    "price": str(menu_item.price),
                }
            )

        order = Order.objects.create(
            restaurant=restaurant, table=table, total_amount=total
        )

        for oi in order_items:
            oi.order = order
        OrderItem.objects.bulk_create(order_items)

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "kitchen",
            {
                "type": "send_notification",
                "message": f"🔥 Table {table.table_number} placed Order #{str(order.id)[-4:]}",
                "order_data": {
                    "id": str(order.id),
                    "restaurant_name": restaurant.name,
                    "table_number": table.table_number,
                    "status": order.status,
                    "total_amount": str(total),
                    "created_at": order.created_at.isoformat(),
                    "items": order_items_data,
                },
            },
        )

        response_serializer = TableOrderCreateResponseSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OrderStatusView(APIView):
    permission_classes = []

    def get(self, request, order_id):

        order = Order.objects.select_related("table").filter(id=order_id).first()

        if not order:
            return Response(
                {"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = OrderStatusSerializer(order)

        return Response(serializer.data, status=status.HTTP_200_OK)


class KitchenOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        restaurant = request.user.owned_restaurant

        if not restaurant:
            return Response(
                {"detail": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND
            )

        orders = (
            Order.objects.filter(
                restaurant=restaurant,
                is_active=True,
                status__in=["PLACED", "PREPARING", "READY"],
            )
            .select_related("table", "restaurant")
            .prefetch_related("items__menu_item")
            .order_by("-created_at")[:50]
        )

        serializer = KitchenOrdersResponseSerializer(orders, many=True)

        return Response(
            {"restaurant_name": restaurant.name, "orders": serializer.data},
            status=status.HTTP_200_OK,
        )


class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        try:
            order = (
                Order.objects.select_related("table", "restaurant")
                .prefetch_related("items__menu_item")
                .get(id=order_id)
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if order.restaurant != request.user.owned_restaurant:
            return Response(
                {"detail": "You don't have permission to update this order"},
                status=status.HTTP_403_FORBIDDEN,
            )

        new_status = request.data.get("status")

        valid_statuses = ["PLACED", "PREPARING", "READY", "SERVED", "CANCELLED"]
        if new_status not in valid_statuses:
            return Response(
                {
                    "detail": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        order.status = new_status
        order.save()

        if new_status in ["SERVED", "CANCELLED"]:
            order.is_active = False
            order.save()

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "kitchen",
            {
                "type": "send_notification",
                "message": f"Order #{str(order.id)[-4:]} status updated to {new_status}",
                "order_id": str(order.id),
                "status": new_status,
                "table_number": order.table.table_number,
            },
        )

        serializer = UpdateOrderStatusResponseSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        restaurant = request.user.owned_restaurant

        if not restaurant:
            return Response(
                {"detail": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND
            )

        status_filter = request.query_params.get("status")

        orders = (
            Order.objects.filter(restaurant=restaurant)
            .select_related("table")
            .prefetch_related("items__menu_item")
            .order_by("-created_at")
        )

        if status_filter:
            orders = orders.filter(status=status_filter)

        serializer = AdminOrderListSerializer(orders, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):

        order = (
            Order.objects.select_related("table", "restaurant")
            .prefetch_related("items__menu_item")
            .filter(id=order_id)
            .first()
        )

        if not order:
            return Response(
                {"detail": "Order not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if order.restaurant != request.user.owned_restaurant:
            return Response(
                {"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = AdminOrderDetailSerializer(order)

        return Response(serializer.data, status=status.HTTP_200_OK)
