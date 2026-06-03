import json
import os
import boto3
import urllib.request
from datetime import datetime, timezone

from decimal import Decimal

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb")

# Get table name from environment variable
table = dynamodb.Table(os.environ["DYNAMODB_TABLE"])


# Get API key and city
API_KEY = os.environ["OPENWEATHER_API_KEY"]
CITY = os.environ.get("CITY", "Kochi")

def lambda_handler(event, context):
    
    # OpenWeather API URL
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={CITY}&appid={API_KEY}&units=metric"
    )