import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


from analytics_pipeline.producers.python.analytics_producer import AnalyticsProducer
from menu.models import MenuItem
from restaurants.models import Table
from .models import Order, OrderItem

from .serializers import (
    AdminOrderDetailSerializer,
    AdminOrderListSerializer,
    KitchenOrderSerializer,
    OrderStatusSerializer,
    TableOrderCreateResponseSerializer,
    TableOrderCreateSerializer,
    UpdateOrderStatusResponseSerializer,
)

# =========================================================
# 🔥 CREATE ORDER (Customer → QR → Order)
# =========================================================

class TableOrderCreateView(APIView):
    permission_classes = []

    @transaction.atomic
    def post(self, request, table_id):

        serializer = TableOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        table = Table.objects.select_related("restaurant").filter(id=table_id).first()

        if not table:
            return Response({"detail": "Invalid table"}, status=404)

        restaurant = table.restaurant

        total = 0
        order_items = []

        # Validate items
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
                    status=400,
                )

            qty = item["quantity"]
            total += menu_item.price * qty

            order_items.append(
                OrderItem(
                    menu_item=menu_item,
                    quantity=qty,
                    price=menu_item.price,
                )
            )

        # Create order
        order = Order.objects.create(
            restaurant=restaurant,
            table=table,
            total_amount=total,
        )

        for oi in order_items:
            oi.order = order

        OrderItem.objects.bulk_create(order_items)

        # 🔥 REALTIME NOTIFY AFTER COMMIT (FIXED)

        def notify_kitchen():

            fresh_order = (
                Order.objects.select_related("table", "restaurant")
                .prefetch_related("items__menu_item")
                .get(id=order.id)
            )

            order_data = KitchenOrderSerializer(fresh_order).data

            try:
                requests.post(
                    "http://notification:8001/notification/notify_kitchen/",
                    json={
                        "restaurant_id": restaurant.id,
                        "event": "new_order",
                        "order": order_data,
                    },
                    timeout=2,
                )
            except Exception as e:
                print("Notification failed:", e)

        transaction.on_commit(notify_kitchen)

        return Response(
            TableOrderCreateResponseSerializer(order).data,
            status=201
        )

# =========================================================
# 🔥 CUSTOMER ORDER STATUS
# =========================================================

class OrderStatusView(APIView):
    permission_classes = []

    def get(self, request, order_id):

        order = Order.objects.select_related("table").filter(id=order_id).first()

        if not order:
            return Response({"detail": "Order not found"}, status=404)

        serializer = OrderStatusSerializer(order)
        return Response(serializer.data, status=200)


# =========================================================
# 🔥 KITCHEN ACTIVE ORDERS
# =========================================================

class KitchenOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        restaurant = request.user.owned_restaurant

        if not restaurant:
            return Response({"detail": "Restaurant not found"}, status=404)

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

        serializer = KitchenOrderSerializer(orders, many=True)
        return Response(serializer.data, status=200)
    

# =========================================================
# 🔥 WAITER READY ORDERS (DATABASE)
# =========================================================

class WaiterOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        restaurant = request.user.owned_restaurant

        if not restaurant:
            return Response({"detail": "Restaurant not found"}, status=404)

        orders = (
            Order.objects.filter(
                restaurant=restaurant,
                status="READY",     # 🔥 ONLY READY
                is_active=True,
            )
            .select_related("table", "restaurant")
            .prefetch_related("items__menu_item")
            .order_by("-created_at")
        )

        serializer = KitchenOrderSerializer(orders, many=True)
        return Response(serializer.data, status=200)


# =========================================================
# 🔥 UPDATE ORDER STATUS
# =========================================================

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
            return Response({"detail": "Order not found"}, status=404)

        if order.restaurant != request.user.owned_restaurant:
            return Response({"detail": "Permission denied"}, status=403)

        new_status = request.data.get("status")

        valid_statuses = ["PLACED", "PREPARING", "READY", "SERVED", "CANCELLED"]

        if new_status not in valid_statuses:
            return Response({"detail": "Invalid status"}, status=400)

        order.status = new_status

        if new_status in ["SERVED", "CANCELLED"]:
            order.is_active = False

        order.save()

        fresh_order = (
            Order.objects.select_related("table", "restaurant")
            .prefetch_related("items__menu_item")
            .get(id=order.id)
        )

        order_data = KitchenOrderSerializer(fresh_order).data

        # ====================================================
        # 🔥 1️⃣ NOTIFY KITCHEN (always)
        # ====================================================
        try:
            requests.post(
                "http://notification:8001/notification/notify_kitchen/",
                json={
                    "restaurant_id": order.restaurant.id,
                    "event": "order_updated",
                    "order": order_data,
                    "is_active": order.is_active,
                },
                timeout=2,
            )
        except Exception as e:
            print("Kitchen notification failed:", e)

        # ====================================================
        # 🔥 2️⃣ NOTIFY WAITER WHEN READY
        # ====================================================
        if new_status == "READY":
            try:
                requests.post(
                    "http://notification:8001/notification/notify_waiter/",
                    json={
                        "restaurant_id": order.restaurant.id,
                        "event": "order_ready",
                        "message": f"Table {order.table.table_number} — Order Ready",
                        "order": order_data,
                        "order_id":order.id
                    },
                    timeout=2,
                )
            except Exception as e:
                print("Waiter notification failed:", e)

        # ====================================================
        # 🔥 3️⃣ REMOVE FROM WAITER WHEN SERVED
        # ====================================================
        if new_status == "SERVED":
            try:
                requests.post(
                    "http://notification:8001/notification/notify_waiter/",
                    json={
                        "restaurant_id": order.restaurant.id,
                        "event": "order_served",
                        "order_id": order.id,
                    },
                    timeout=2,
                )
            except Exception as e:
                print("Waiter remove failed:", e)

        return Response(
            UpdateOrderStatusResponseSerializer(order).data,
            status=200
        )

# =========================================================
# 🔥 ADMIN VIEWS
# =========================================================

class AdminOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        restaurant = request.user.owned_restaurant

        if not restaurant:
            return Response({"detail": "Restaurant not found"}, status=404)

        orders = (
            Order.objects.filter(restaurant=restaurant)
            .select_related("table")
            .prefetch_related("items__menu_item")
            .order_by("-created_at")
        )

        serializer = AdminOrderListSerializer(orders, many=True)
        return Response(serializer.data, status=200)


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
            return Response({"detail": "Order not found"}, status=404)

        if order.restaurant != request.user.owned_restaurant:
            return Response({"detail": "Permission denied"}, status=403)

        serializer = AdminOrderDetailSerializer(order)
        return Response(serializer.data, status=200)