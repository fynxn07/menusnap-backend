import os
import json
import uuid
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError


class AnalyticsProducer:
    def __init__(self):

        self.queue_url = os.getenv("ANALYTICS_SQS_URL")

        if not self.queue_url:
            raise ValueError("ANALYTICS_SQS_URL not set")

        region = os.getenv("AWS_DEFAULT_REGION", "ap-south-1")

        self.sqs = boto3.client(
            "sqs",
            region_name=region
        )

    def send_event(self, event_type, restaurant_id, data, source="backend"):
        event = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "restaurant_id": restaurant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "version": "1.0",
            "data": data,
        }

        try:
            params = {
                "QueueUrl": self.queue_url,
                "MessageBody": json.dumps(event),
            }

        # 🔥 Handle FIFO queues automatically
            if self.queue_url.endswith(".fifo"):
                params["MessageGroupId"] = "analytics"
                params["MessageDeduplicationId"] = str(uuid.uuid4())

            response = self.sqs.send_message(**params)

            print("✅ SQS EVENT SENT:", response["MessageId"])

        except Exception as e:
            print("❌ SQS SEND FAILED:", str(e))