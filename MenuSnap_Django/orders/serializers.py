from rest_framework import serializers

from menu.models import MenuItem

from .models import Order, OrderItem


class OrderItemSerializer(serializers.Serializer):
    menu_item = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class TableOrderCreateSerializer(serializers.Serializer):
    items = OrderItemSerializer(many=True)

    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("Order must contain items")
        return value


class TableOrderCreateResponseSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="id", read_only=True)
    table_number = serializers.IntegerField(source="table.table_number", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id",
            "table_number",
            "total_amount",
            "status",
        ]


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ["id", "name", "price"]


class KitchenOrderItemSerializer(serializers.ModelSerializer):
    menu_item = MenuItemSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "menu_item", "quantity", "price"]


class KitchenOrderSerializer(serializers.ModelSerializer):
    items = KitchenOrderItemSerializer(many=True, read_only=True)
    table_number = serializers.IntegerField(source="table.table_number", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "restaurant_name",
            "table_number",
            "status",
            "total_amount",
            "created_at",
            "items",
        ]
        read_only_fields = ["id", "created_at"]


class KitchenOrdersResponseSerializer(serializers.Serializer):
    restaurant_name = serializers.CharField()
    orders = KitchenOrderSerializer(many=True)


class OrderStatusSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="id", read_only=True)
    table_number = serializers.IntegerField(source="table.table_number", read_only=True)

    class Meta:
        model = Order
        fields = [
            "order_id",
            "status",
            "table_number",
            "total_amount",
            "created_at",
        ]


class UpdateOrderStatusResponseSerializer(serializers.ModelSerializer):
    order_id = serializers.UUIDField(source="id", read_only=True)
    table_number = serializers.IntegerField(source="table.table_number", read_only=True)
    message = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "message",
            "order_id",
            "status",
            "table_number",
        ]

    def get_message(self, obj):
        return "Order status updated successfully"


class AdminOrderListSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source="table.table_number", read_only=True)
    items_preview = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "table_number",
            "status",
            "total_amount",
            "created_at",
            "items_preview",
        ]

    def get_items_preview(self, obj):
        items = obj.items.select_related("menu_item")[:3]
        return [
            {
                "name": i.menu_item.name if i.menu_item else "Deleted Item",
                "quantity": i.quantity,
            }
            for i in items
        ]


class AdminOrderDetailSerializer(serializers.ModelSerializer):
    table_number = serializers.IntegerField(source="table.table_number", read_only=True)
    restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
    items = KitchenOrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "restaurant_name",
            "table_number",
            "status",
            "total_amount",
            "created_at",
            "items",
        ]


# class RealtimeOrderSerializer(serializers.ModelSerializer):
#     restaurant_name = serializers.CharField(source="restaurant.name", read_only=True)
#     table_number = serializers.IntegerField(source="table.table_number", read_only=True)
#     items = KitchenOrderItemSerializer(many=True, read_only=True)

#     class Meta:
#         model = Order
#         fields = ["id","restaurant_name","table_number","status","total_amount","created_at","items",]
