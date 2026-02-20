from django.shortcuts import render
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from restaurants.models import Restaurant, Table

from .models import MenuCategory, MenuItem
from .serializers import (
    CustomerMenuResponseSerializer,
    MenuCategorySerializer,
    MenuItemSerializer,
    PublicMenuResponseSerializer,
)

# Create your views here.


class MenuCategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = MenuCategory.objects.filter(
            restaurant=request.user.restaurant
        ).order_by("display_order")

        serializer = MenuCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MenuCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(restaurant=request.user.restaurant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MenuCategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        try:
            return MenuCategory.objects.get(id=pk, restaurant=request.user.restaurant)
        except MenuCategory.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(request, pk)
        if not category:
            return Response({"detail": "Category not found"}, status=404)

        serializer = MenuCategorySerializer(category)
        return Response(serializer.data)

    def patch(self, request, pk):
        category = self.get_object(request, pk)
        if not category:
            return Response({"detail": "Category not found"}, status=404)

        serializer = MenuCategorySerializer(category, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        category = self.get_object(request, pk)
        if not category:
            return Response({"detail": "Category not found"}, status=404)

        category.delete()
        return Response({"detail": "Category deleted"})


class MenuItemListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        items = MenuItem.objects.filter(
            restaurant=request.user.restaurant, is_active=True
        )

        category_id = request.query_params.get("category")
        if category_id:
            items = items.filter(category_id=category_id)

        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MenuItemSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save(restaurant=request.user.restaurant)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MenuItemDetailView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_object(self, request, pk):
        try:
            return MenuItem.objects.get(
                id=pk, restaurant=request.user.restaurant, is_active=True
            )
        except MenuItem.DoesNotExist:
            return None

    def get(self, request, pk):
        item = self.get_object(request, pk)
        if not item:
            return Response({"detail": "Menu item not found"}, status=404)

        serializer = MenuItemSerializer(item)
        return Response(serializer.data)

    def patch(self, request, pk):
        item = self.get_object(request, pk)
        if not item:
            return Response({"detail": "Menu item not found"}, status=404)

        serializer = MenuItemSerializer(
            item, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, pk):
        item = self.get_object(request, pk)
        if not item:
            return Response({"detail": "Menu item not found"}, status=404)

        item.is_active = False
        item.save(update_fields=["is_active"])

        return Response({"detail": "Menu item deleted"})


class CustomerMenuView(APIView):
    permission_classes = []

    def get(self, request, restaurant_id, table_id):

        restaurant = Restaurant.objects.filter(id=restaurant_id).first()
        if not restaurant:
            return Response({"detail": "Restaurant not found"}, status=404)

        table = Table.objects.filter(id=table_id, restaurant=restaurant).first()
        if not table:
            return Response({"detail": "Table not found"}, status=404)

        items = MenuItem.objects.filter(
            restaurant=restaurant, is_active=True, is_available=True
        ).select_related("category")

        data = {"restaurant": restaurant, "table": table, "items": items}

        serializer = CustomerMenuResponseSerializer(data)
        return Response(serializer.data)


class PublicMenuView(APIView):
    permission_classes = []

    def get(self, request, restaurant_id):
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, is_active=True)
        except Restaurant.DoesNotExist:
            return Response(
                {"detail": "Restaurant not found"}, status=status.HTTP_404_NOT_FOUND
            )

        categories = MenuCategory.objects.filter(
            restaurant=restaurant, is_active=True
        ).order_by("display_order")

        data = {"restaurant": restaurant, "categories": categories}

        serializer = PublicMenuResponseSerializer(data)
        return Response(serializer.data)


class MenuStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        restaurant = request.user.restaurant

        total_items = MenuItem.objects.filter(
            restaurant=restaurant, is_active=True
        ).count()

        limit = 30  # free plan

        return Response(
            {
                "total_items": total_items,
                "limit": limit,
            }
        )
