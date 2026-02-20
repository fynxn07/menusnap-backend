from rest_framework import serializers

from restaurants.models import Restaurant, Table

from .models import MenuCategory, MenuItem


class MenuCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuCategory
        fields = [
            "id",
            "name",
            "is_active",
            "display_order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MenuItemSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False, allow_null=True)

    category = serializers.PrimaryKeyRelatedField(
        queryset=MenuCategory.objects.all(), write_only=True
    )

    category_detail = MenuCategorySerializer(source="category", read_only=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "category",
            "category_detail",
            "name",
            "description",
            "price",
            "is_veg",
            "is_available",
            "display_order",
            "image",
        ]
        read_only_fields = ["id"]

    def validate(self, data):
        request = self.context["request"]
        restaurant = request.user.restaurant

        category = data.get("category")
        name = data.get("name")

        item_id = self.instance.id if self.instance else None

        exists = (
            MenuItem.objects.filter(
                restaurant=restaurant, category=category, name__iexact=name
            )
            .exclude(id=item_id)
            .exists()
        )

        if exists:
            raise serializers.ValidationError(
                {"name": "Item with this name already exists in this category."}
            )

        return data


class CustomerMenuItemSerializer(serializers.ModelSerializer):
    category = MenuCategorySerializer(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "description",
            "price",
            "image",
            "is_veg",
            "is_available",
            "category",
        ]


class CustomerMenuRestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["id", "name"]


class CustomerMenuTableSerializer(serializers.ModelSerializer):
    number = serializers.IntegerField(source="table_number")

    class Meta:
        model = Table
        fields = ["id", "number"]


class CustomerMenuResponseSerializer(serializers.Serializer):
    restaurant = CustomerMenuRestaurantSerializer()
    table = CustomerMenuTableSerializer()
    items = CustomerMenuItemSerializer(many=True)


class PublicMenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = [
            "id",
            "name",
            "description",
            "price",
            "is_veg",
        ]


class PublicMenuCategorySerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = MenuCategory
        fields = ["id", "name", "items"]

    def get_items(self, obj):
        items = MenuItem.objects.filter(
            category=obj, is_active=True, is_available=True
        ).order_by("display_order")

        return PublicMenuItemSerializer(items, many=True).data


class PublicRestaurantSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "id",
            "name",
            "logo",
            "theme",
            "primary_color",
            "secondary_color",
        ]

    def get_logo(self, obj):
        return obj.logo.url if obj.logo else None


class PublicMenuResponseSerializer(serializers.Serializer):
    restaurant = PublicRestaurantSerializer()
    categories = PublicMenuCategorySerializer(many=True)
