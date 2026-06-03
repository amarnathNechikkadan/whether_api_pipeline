import json
import os
import boto3
from datetime import datetime, timezone
from decimal import Decimal

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["S3_BUCKET"]

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    records_to_save = []
    
    for record in event["Records"]:
        if record["eventName"] == "INSERT":
            new_image = record["dynamodb"]["NewImage"]

            item = {
                "city": new_image["city"]["S"],
                "timestamp": new_image["timestamp"]["S"],
                "temperature": float(new_image["temperature"]["N"]),
                "humidity": float(new_image["humidity"]["N"]),
                "weather": new_image["weather"]["S"],
                "wind_speed": float(new_image["wind_speed"]["N"]),
                "raw_data": new_image["raw_data"]["S"]
            }
            
            records_to_save.append(item)