import boto3
from boto3.dynamodb.conditions import Key
from django.conf import settings


class DynamoDBService:
    def __init__(self):
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.AWS_DEFAULT_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE)

    # =====================================================
    # 💰 REVENUE
    # =====================================================
    def get_revenue(self, restaurant_id):
        response = self.table.get_item(
            Key={
                "PK": f"RESTAURANT#{restaurant_id}",
                "SK": "METRIC#REVENUE",
            }
        )
        item = response.get("Item")
        return float(item.get("total_revenue", 0)) if item else 0

    # =====================================================
    # 📦 TOTAL ORDERS
    # =====================================================
    def get_total_orders(self, restaurant_id):
        response = self.table.get_item(
            Key={
                "PK": f"RESTAURANT#{restaurant_id}",
                "SK": "METRIC#ORDERS",
            }
        )
        item = response.get("Item")
        return int(item.get("total_orders", 0)) if item else 0

    # =====================================================
    # ⏰ PEAK HOURS
    # =====================================================
    def get_peak_hours(self, restaurant_id):
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"RESTAURANT#{restaurant_id}")
        )

        hours = []

        for item in response.get("Items", []):
            sk = item["SK"]
            if sk.startswith("METRIC#HOUR#"):
                hour = int(sk.split("#")[-1])
                count = int(item.get("order_count", 0))
                hours.append({"hour": hour, "orders": count})

        peak_hour = max(hours, key=lambda x: x["orders"])["hour"] if hours else None

        return {
            "peak_hour": peak_hour,
            "hours": sorted(hours, key=lambda x: x["hour"])
        }

    # =====================================================
    # 📈 ORDER TRENDS
    # =====================================================
    def get_order_trends(self, restaurant_id):
        total_orders = self.get_total_orders(restaurant_id)
        return {"total_orders": total_orders}

    # =====================================================
    # 🍔 POPULAR DISHES
    # =====================================================
    def get_popular_dishes(self, restaurant_id):
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"RESTAURANT#{restaurant_id}")
        )

        dishes = []

        for item in response.get("Items", []):
            sk = item["SK"]
            if sk.startswith("METRIC#DISH#"):
                dish_id = sk.split("#")[-1]
                count = int(item.get("add_count", 0))
                dishes.append({
                    "item_id": dish_id,
                    "orders": count
                })

        dishes.sort(key=lambda x: x["orders"], reverse=True)

        return {"top_items": dishes[:5]}

    # =====================================================
    # 🪑 TABLE UTILIZATION
    # =====================================================
    def get_table_utilization(self, restaurant_id):
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"RESTAURANT#{restaurant_id}")
        )

        tables = {}

        for item in response.get("Items", []):
            if item["SK"].startswith("EVENT#"):
                data = item.get("data", {})
                table_no = data.get("table_number")

                if table_no:
                    tables[table_no] = tables.get(table_no, 0) + 1

        result = [
            {"table_number": k, "orders": v}
            for k, v in tables.items()
        ]

        result.sort(key=lambda x: x["orders"], reverse=True)

        return {"tables": result[:5]}

    # =====================================================
    # 📜 RAW EVENTS (FOR DEBUG)
    # =====================================================
    def get_events(self, restaurant_id):
        response = self.table.query(
            KeyConditionExpression=Key("PK").eq(f"RESTAURANT#{restaurant_id}")
        )

        events = [
            item for item in response.get("Items", [])
            if item["SK"].startswith("EVENT#")
        ]

        return events