import json
import os
import boto3
from datetime import datetime, timezone
from decimal import Decimal

s3 = boto3.client("s3")
BUCKET_NAME = os.environ["S3_BUCKET"]