from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services.dynamodb_service import DynamoDBService


# =====================================================
# 📜 RAW EVENTS (DEBUG / OPTIONAL)
# =====================================================
class RestaurantEventsView(APIView):
    def get(self, request, restaurant_id):
        service = DynamoDBService()
        events = service.get_events(restaurant_id)

        return Response({
            "restaurant_id": restaurant_id,
            "events": events
        }, status=status.HTTP_200_OK)


# =====================================================
# 💰 REVENUE + TOTAL ORDERS
# =====================================================
class RevenueView(APIView):
    def get(self, request, restaurant_id):
        service = DynamoDBService()

        total_revenue = service.get_revenue(restaurant_id)
        total_orders = service.get_total_orders(restaurant_id)

        return Response({
            "total_revenue": total_revenue,
            "total_orders": total_orders
        }, status=status.HTTP_200_OK)


# =====================================================
# ⏰ PEAK HOURS
# =====================================================
class PeakHoursView(APIView):
    def get(self, request, restaurant_id):
        service = DynamoDBService()
        data = service.get_peak_hours(restaurant_id)

        return Response(data, status=status.HTTP_200_OK)


# =====================================================
# 📈 ORDER TRENDS
# =====================================================
class OrderTrendsView(APIView):
    def get(self, request, restaurant_id):
        service = DynamoDBService()
        data = service.get_order_trends(restaurant_id)

        return Response(data, status=status.HTTP_200_OK)


# =====================================================
# 🍔 POPULAR DISHES
# =====================================================
class PopularDishesView(APIView):
    def get(self, request, restaurant_id):
        service = DynamoDBService()
        data = service.get_popular_dishes(restaurant_id)

        return Response(data, status=status.HTTP_200_OK)


# =====================================================
# 🪑 TABLE UTILIZATION
# =====================================================
class TableUtilizationView(APIView):
    def get(self, request, restaurant_id):
        service = DynamoDBService()
        data = service.get_table_utilization(restaurant_id)

        return Response(data, status=status.HTTP_200_OK)