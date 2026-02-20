from rest_framework import serializers

from .models import Restaurant, Table


class RestaurantOnboardingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            "name",
            "restaurant_type",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "country",
        ]
        read_only_fields = []


class RestaurantBrandingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = [
            "logo",
            "primary_color",
            "secondary_color",
            "theme",
        ]


class TableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Table
        fields = ["id", "table_number", "qr_code"]
        read_only_fields = ["id", "qr_code"]


class BulkTableCreateSerializer(serializers.Serializer):
    total_tables = serializers.IntegerField(min_value=1, max_value=500)


class RestaurantLogoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ["logo"]
