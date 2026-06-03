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