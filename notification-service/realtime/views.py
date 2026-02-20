from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class NotifyKitchenView(APIView):

    def post(self, request):
        message = request.data.get("message")

        if not message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "kitchen",
            {
                "type": "send_notification",
                "message": message,
            }
        )

        return Response(
            {"status": "sent to kitchen"},
            status=status.HTTP_200_OK
        )


class NotifyWaiterView(APIView):

    def post(self, request):
        message = request.data.get("message")

        if not message:
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            "waiter",
            {
                "type": "send_notification",
                "message": message,
            }
        )

        return Response(
            {"status": "sent to waiter"},
            status=status.HTTP_200_OK
        )
