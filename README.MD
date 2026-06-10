# Weather Data Pipeline

This project is an end-to-end cloud data pipeline that collects real-time weather data from the OpenWeather API, stores it in AWS DynamoDB, processes DynamoDB Stream records using AWS Lambda, saves the processed data into Amazon S3 as JSON files, and finally loads the data into Snowflake for analytics.

## Architecture

```text
EventBridge
   ↓
Lambda Function 1
   ↓
OpenWeather API
   ↓
DynamoDB
   ↓
DynamoDB Streams
   ↓
Lambda Function 2
   ↓
Amazon S3
   ↓
Snowflake
```

## Technologies Used

* AWS Lambda
* Amazon DynamoDB
* DynamoDB Streams
* Amazon S3
* Amazon EventBridge
* Snowflake
* Python
* Boto3
* OpenWeather API
* JSON

## Project Workflow

### 1. EventBridge Trigger

Amazon EventBridge is used to run the first Lambda function automatically at a scheduled time.

This makes the weather data collection automated instead of manually running the code.

### 2. Lambda Function 1: Fetch Weather Data

The first Lambda function fetches current weather data from the OpenWeather API.

It uses environment variables for secure configuration:

```python
API_KEY = os.environ["OPENWEATHER_API_KEY"]
CITY = os.environ.get("CITY", "Kochi")
```

`OPENWEATHER_API_KEY` stores the API key securely.

`CITY` stores the city name. If no city is provided, the default city is Kochi.

The API URL is created using the city and API key:

```python
url = (
    f"https://api.openweathermap.org/data/2.5/weather"
    f"?q={CITY}&appid={API_KEY}&units=metric"
)
```

The `units=metric` parameter returns temperature in Celsius.

The API response is read and converted into JSON:

```python
with urllib.request.urlopen(url) as response:
    data = json.loads(response.read().decode())
```

### 3. Store Weather Data in DynamoDB

The weather data is prepared as a DynamoDB item:

```python
item = {
    "city": CITY,
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "temperature": Decimal(str(data["main"]["temp"])),
    "humidity": Decimal(str(data["main"]["humidity"])),
    "weather": data["weather"][0]["description"],
    "wind_speed": Decimal(str(data["wind"]["speed"])),
    "raw_data": json.dumps(data)
}
```

DynamoDB does not support normal Python float values directly, so `Decimal` is used for numeric fields.

The item is inserted into DynamoDB:

```python
table.put_item(Item=item)
```

### 4. DynamoDB Streams

DynamoDB Streams capture new records inserted into the table.

When new weather data is inserted, the stream triggers the second Lambda function.

Only `INSERT` events are processed:

```python
if record["eventName"] == "INSERT":
```

This means the Lambda function only handles newly added records.

### 5. Lambda Function 2: Process Stream Records

The second Lambda function reads the new DynamoDB stream records.

It extracts values from the DynamoDB stream format:

```python
item = {
    "city": new_image["city"]["S"],
    "timestamp": new_image["timestamp"]["S"],
    "temperature": float(new_image["temperature"]["N"]),
    "humidity": float(new_image["humidity"]["N"]),
    "weather": new_image["weather"]["S"],
    "wind_speed": float(new_image["wind_speed"]["N"]),
    "raw_data": new_image["raw_data"]["S"]
}
```

DynamoDB Stream values contain data types such as:

* `S` for string
* `N` for number

The processed records are added to a list:

```python
records_to_save.append(item)
```

### 6. Save Data to Amazon S3

The second Lambda function saves the processed weather records into S3 as JSON files.

The file path is partitioned by year, month, and day:

```python
file_name = f"weather-data/year={now.year}/month={now.month}/day={now.day}/weather_{now.strftime('%H-%M-%S')}.json"
```

Example S3 path:

```text
weather-data/year=2026/month=6/day=10/weather_10-30-15.json
```

This partitioned structure is useful for analytics and querying large datasets.

The file is uploaded to S3:

```python
s3.put_object(
    Bucket=BUCKET_NAME,
    Key=file_name,
    Body=json.dumps(records_to_save, default=decimal_default),
    ContentType="application/json"
)
```

### 7. Snowflake Setup

Snowflake is used to load and analyze the weather JSON data stored in S3.

A JSON file format is created:

```sql
CREATE OR REPLACE FILE FORMAT WEATHER_JSON_FORMAT
TYPE = JSON;
```

A raw table is created using the `VARIANT` data type:

```sql
CREATE OR REPLACE TABLE WEATHER_RAW (
    RAW_DATA VARIANT
);
```

`VARIANT` is used because the source data is semi-structured JSON.

An external stage is created to connect Snowflake with the S3 bucket:

```sql
CREATE OR REPLACE STAGE WEATHER_S3_STAGE
URL = 's3://your-bucket-name/weather-data/'
CREDENTIALS = (
  AWS_KEY_ID = 'YOUR_ACCESS_KEY'
  AWS_SECRET_KEY = 'YOUR_SECRET_KEY'
)
FILE_FORMAT = WEATHER_JSON_FORMAT;
```

Weather data is loaded into Snowflake:

```sql
COPY INTO WEATHER_RAW
FROM @WEATHER_S3_STAGE
FILE_FORMAT = WEATHER_JSON_FORMAT;
```

The loaded data can be verified using:

```sql
SELECT * FROM WEATHER_RAW;
```

## Project Files

```text
weather-data-pipeline/
│
├── lambda/
│   ├── lambda_fetch_api.py
│   └── dynamodb_to_s3.py
│
├── snowflake_setup.sql
├── requirements.txt
├── .gitignore
└── README.md
```

## File Explanation

### `lambda/lambda_fetch_api.py`

This file contains the first Lambda function.

Main responsibilities:

* Connect to DynamoDB
* Read environment variables
* Fetch weather data from OpenWeather API
* Convert numeric values using `Decimal`
* Store weather data into DynamoDB

### `lambda/dynamodb_to_s3.py`

This file contains the second Lambda function.

Main responsibilities:

* Read DynamoDB Stream records
* Process only new insert records
* Convert DynamoDB stream format into normal JSON
* Store processed weather records in S3
* Save files using partitioned folder structure

### `snowflake_setup.sql`

This file contains Snowflake SQL commands.

Main responsibilities:

* Create JSON file format
* Create raw weather table
* Create external S3 stage
* Load JSON data from S3 into Snowflake
* Verify loaded records

### `requirements.txt`

This file contains Python dependencies required for the project.

Example:

```text
boto3
requests
```

### `.gitignore`

This file prevents unnecessary or sensitive files from being committed.

Example:

```text
.env
__pycache__/
*.zip
```

`.env` is ignored because it may contain API keys or secret credentials.

## Environment Variables

### Lambda Function 1

```text
DYNAMODB_TABLE=your-dynamodb-table-name
OPENWEATHER_API_KEY=your-openweather-api-key
CITY=Kochi
```

### Lambda Function 2

```text
S3_BUCKET=your-s3-bucket-name
```

## Why Decimal Is Used

DynamoDB does not accept Python float values directly.

So this code:

```python
Decimal(str(data["main"]["temp"]))
```

converts weather temperature into a DynamoDB-compatible number format.

## Why DynamoDB Streams Are Used

DynamoDB Streams allow the pipeline to react automatically whenever a new item is inserted.

This avoids manually running the second Lambda function.

## Why S3 Partitioning Is Used

The S3 path uses this structure:

```text
year/month/day
```

This helps organize data clearly and makes future analytics easier.

## Future Improvements

* Add Snowpipe for automatic Snowflake ingestion
* Build a Streamlit dashboard
* Add data visualization
* Add error handling and logging
* Store API secrets in AWS Secrets Manager
* Add CI/CD deployment using GitHub Actions

## Project Status

The basic pipeline is completed:

* Weather data is fetched from OpenWeather API
* Data is stored in DynamoDB
* DynamoDB Stream triggers Lambda
* Processed data is saved to S3
* Snowflake SQL setup is added for loading data
