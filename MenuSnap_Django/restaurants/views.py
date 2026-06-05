from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Table
from .serializers import (
    BulkTableCreateSerializer,
    RestaurantBrandingSerializer,
    RestaurantLogoSerializer,
    RestaurantOnboardingSerializer,
    TableSerializer,
)
from .utils import generate_qr_code


# Create your views here.
class RestaurantOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        restaurant = request.user.restaurant or getattr(
            request.user, "owned_restaurant", None
        )

        if not restaurant:
            raise ValidationError("Restaurant not found for this user")

        serializer = RestaurantOnboardingSerializer(
            restaurant, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


class RestaurantBrandingView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        user = request.user
        restaurant = user.restaurant or getattr(user, "owned_restaurant", None)

        if not restaurant:
            raise ValidationError("Restaurant not found for this user")

        serializer = RestaurantBrandingSerializer(
            restaurant, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if not user.restaurant:
            user.restaurant = restaurant
            user.save(update_fields=["restaurant"])

        return Response(serializer.data, status=status.HTTP_200_OK)


class BulkTableCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        restaurant = user.restaurant or getattr(user, "owned_restaurant", None)

        if not restaurant:
            raise ValidationError("Restaurant not found")

        serializer = BulkTableCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        total_tables = serializer.validated_data["total_tables"]

        created_tables = []

        for table_number in range(1, total_tables + 1):
            table, created = Table.objects.get_or_create(
                restaurant=restaurant, table_number=table_number
            )

            qr_url = f"{settings.FRONTEND_URL}/menu/{restaurant.id}?code={table.manual_code}"
            qr_image = generate_qr_code(qr_url)
            table.qr_code.save(f"table_{table_number}.png", qr_image)

            created_tables.append(table)

        return Response(
            TableSerializer(created_tables, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class CompleteOnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        restaurant = request.user.restaurant

        if not restaurant:
            return Response(
                {"detail": "Restaurant not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        restaurant.is_onboarding_completed = True
        restaurant.save()

        return Response({"detail": "Onboarding completed"}, status=status.HTTP_200_OK)


class RestaurantLogoUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        restaurant = request.user.restaurant

        if not restaurant:
            return Response(
                {"error": "Restaurant not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RestaurantLogoSerializer(
            restaurant, data=request.data, partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Logo uploaded successfully", "logo_url": restaurant.logo.url},
            status=status.HTTP_200_OK,
        )


class JoinTableView(APIView):
    permission_classes = []

    def post(self, request):
        code = request.data.get("manual_code")

        table = Table.objects.filter(
            manual_code=code.upper()
        ).select_related("restaurant").first()

        if not table:
            return Response(
                {"error": "Invalid table code"},
                status=404
            )

        return Response({
            "restaurant_id": table.restaurant.id,
            "table_id": str(table.id),
            "table_number": table.table_number,
        })