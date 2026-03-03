from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


# =========================================================
# 🔥 KITCHEN NOTIFICATIONS
# =========================================================

class NotifyKitchenView(APIView):

    def post(self, request):

        restaurant_id = request.data.get("restaurant_id")
        event = request.data.get("event")
        order = request.data.get("order")

        if not restaurant_id:
            return Response(
                {"error": "restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not event:
            return Response(
                {"error": "event is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        group_name = f"kitchen_{restaurant_id}"

        channel_layer = get_channel_layer()

        payload = {
            "type": "send_notification",
            "event": event,
            "order": order,
            "is_active": request.data.get("is_active", True),
        }

        async_to_sync(channel_layer.group_send)(
            group_name,
            payload
        )
        
        print("🔥 Sent to group:", group_name, payload)

        return Response(
            {"status": f"sent to {group_name}"},
            status=status.HTTP_200_OK
        )


# =========================================================
# 🔥 WAITER NOTIFICATIONS
# =========================================================

class NotifyWaiterView(APIView):

    def post(self, request):

        restaurant_id = request.data.get("restaurant_id")
        event = request.data.get("event")
        message = request.data.get("message")
        order = request.data.get("order")
        order_id = request.data.get("order_id")

        if not restaurant_id:
            return Response(
                {"error": "restaurant_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        group_name = f"waiter_{restaurant_id}"

        channel_layer = get_channel_layer()

        payload = {
            "type": "send_notification",
            "event": event or "waiter_notification",
            "message": message or "",
            "order": order,        # 🔥 IMPORTANT
            "order_id": order_id,  # 🔥 IMPORTANT
        }

        async_to_sync(channel_layer.group_send)(
            group_name,
            payload
        )

        print("🔥 Sent to waiter group:", group_name, payload)

        return Response(
            {"status": f"sent to {group_name}"},
            status=status.HTTP_200_OK
        )