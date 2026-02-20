from django.db import transaction
from rest_framework import serializers

from restaurants.models import Restaurant

from .models import User


class UserProfileSerializer(serializers.ModelSerializer):
    is_onboarding_completed = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "role",
            "profile_image",
            "created_at",
            "is_onboarding_completed",
        ]

    def get_is_onboarding_completed(self, obj):  # current user
        if obj.restaurant:
            return obj.restaurant.is_onboarding_completed
        return False

    def get_profile_image(self, obj):
        return obj.profile_image.url if obj.profile_image else None


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RestaurantRegisterSerializer(serializers.Serializer):
    restaurant_name = serializers.CharField(max_length=150)
    owner_name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already Registered")
        return value

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        if len(value) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits")
        return value

    def validate(self, password):
        if password["password"] != password["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match"}
            )
        return password

    @transaction.atomic
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data["owner_name"],
        )
        user.role = user.Role.RESTAURANT_ADMIN
        user.save()

        restaurant = Restaurant.objects.create(
            name=validated_data["restaurant_name"], owner=user
        )

        user.restaurant = restaurant
        user.save()

        return user


class UserUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["name", "phone", "profile_image"]


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField()
    new_password = serializers.CharField()

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Wrong password")
        return value


class RequestOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ResetPasswordSerializer(serializers.Serializer):
    session_token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=6)
