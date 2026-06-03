import json
import os
import boto3
import urllib.request
from datetime import datetime, timezone

from decimal import Decimal

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb")
