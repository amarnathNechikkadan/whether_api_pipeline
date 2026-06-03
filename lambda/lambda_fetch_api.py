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