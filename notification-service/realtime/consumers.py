from channels.generic.websocket import AsyncWebsocketConsumer
import json

class NotificationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_name = self.scope["url_route"]["kwargs"]["group"]

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        await self.send(text_data=json.dumps({
            "message": f"Connected to {self.group_name} group ✅"
        }))



    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        
    async def receive(self, text_data):
        data = json.loads(text_data)

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send_notification",
                "message": data["message"]
            }
        )


    async def send_notification(self, event):
        response_data = {
            "message": event["message"]
        }
        
        if "order_id" in event:
            response_data["type"] = "order_updated"
            response_data["order_id"] = event["order_id"]
            response_data["status"] = event.get("status")
            response_data["table_number"] = event.get("table_number")
        
        if "order_data" in event:
            response_data["type"] = "new_order"
            response_data["order"] = event["order_data"]
        
        await self.send(text_data=json.dumps(response_data))