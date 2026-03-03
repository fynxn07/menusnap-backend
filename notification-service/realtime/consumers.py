from channels.generic.websocket import AsyncWebsocketConsumer
import json


class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = self.scope["url_route"]["kwargs"]["group"]

        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        
        print("🔥 JOINED GROUP:", self.group_name)

        # Confirm connection
        await self.send(text_data=json.dumps({
            "event": "system",
            "message": f"Connected to {self.group_name}"
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Optional debug echo
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_notification",
                "event": "client_message",
                "message": data.get("message", "")
            }
        )

    # 🔥 THIS METHOD NAME MUST MATCH group_send "type"
    async def send_notification(self, event):

        event_type = event.get("event", "unknown")

        response = {"event": event_type}

        if event_type == "new_order":
            response["order"] = event.get("order")

        elif event_type == "order_updated":
            response["order"] = event.get("order")
            response["is_active"] = event.get("is_active", True)

        elif event_type == "order_removed":
            response["order_id"] = event.get("order_id")
            
        elif event_type == "order_ready":
            response["message"] = event.get("message", "")
            response["order"] = event.get("order")

        elif event_type == "order_served":
            response["order_id"] = event.get("order_id")

        else:
            response["message"] = event.get("message", "")

        await self.send(text_data=json.dumps(response))