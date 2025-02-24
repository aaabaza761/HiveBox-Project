"""
Flask application to serve temperature data with Prometheus metrics and Valkey caching.
"""

from datetime import datetime, timedelta, timezone
import requests
import json
import redis
from flask import Flask, jsonify
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
import boto3
import time
import threading

app = Flask(__name__)


# OpenSenseMap API URL
SENSEBOX_API_URL = "https://api.opensensemap.org/boxes"

# Connect to Valkey (running in the Kubernetes cluster)
valkey_client = redis.Redis(host="valkey-service", port=6379, decode_responses=True)

# Prometheus Metrics
REQUEST_COUNT = Counter('temperature_requests_total', 'Total number of temperature requests')
TEMPERATURE_GAUGE = Gauge('average_temperature', 'Average temperature over the last hour')

# MinIO Configuration
MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password"
MINIO_ENDPOINT = "http://minio-service:9000"
MINIO_BUCKET_NAME = "hivebox-storage"

# Create MinIO client
minio_client = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY
)

# Ensure bucket exists
def ensure_bucket():
    """
    Ensures that the required bucket exists in MinIO.
    """
    try:
        minio_client.head_bucket(Bucket=MINIO_BUCKET_NAME)
    except:
        minio_client.create_bucket(Bucket=MINIO_BUCKET_NAME)

# Call the function at startup
ensure_bucket()

def get_temperature_data():
    """
    Fetches temperature data from the openSenseMap API, with caching in Valkey.
    """
    cache_key = "temperature_data"
    
    # Check if data is in Valkey cache
    cached_data = valkey_client.get(cache_key)
    if cached_data:
        try:
            return float(cached_data)  # لو رقم، رجعه مباشرة
        except ValueError:
            return json.loads(cached_data)  # لو JSON، حمّله
    # If no data in cache, fetch from API
    response = requests.get(SENSEBOX_API_URL, timeout=30)
    if response.status_code == 200:
        data = response.json()
        valkey_client.setex(cache_key, 300, json.dumps(data))  # Store in Valkey for 300 seconds
        return data
    
    # If there was an error fetching data, store a default value (float)
    default_data = "50.0"
    valkey_client.setex(cache_key, 300, default_data)  # Store default value in Valkey
    return float(default_data)

def calculate_average_temperature(data):
    """
    Calculates the average temperature from the given data for the last hour.
    """
    now = datetime.now(timezone.utc)
    valid_temperatures = []
    
    for box in data:
        for sensor in box.get('sensors', []):
            if sensor.get('title') != 'Temperatur':
                continue

            last_measurement_at = sensor.get('lastMeasurementAt')
            if not last_measurement_at:
                continue

            try:
                last_measurement_time = datetime.strptime(
                    last_measurement_at, '%Y-%m-%dT%H:%M:%S.%fZ'
                ).replace(tzinfo=timezone.utc)
            except ValueError:
                continue

            if now - last_measurement_time > timedelta(hours=1):
                continue

            temperature = sensor.get('lastMeasurement')
            if temperature:
                valid_temperatures.append(float(temperature))

    if valid_temperatures:
        return sum(valid_temperatures) / len(valid_temperatures)
    return None

def determine_status(temperature):
    """
    Determines the status based on the temperature.
    """
    if temperature < 10:
        return "Too Cold"
    elif 11 <= temperature <= 36:
        return "Good"
    else:
        return "Too Hot"

def store_data_in_minio():
    """
    Fetch temperature data and store it in MinIO.
    """
    data = get_temperature_data()  # جلب البيانات من OpenSenseMap أو الكاش
    if isinstance(data, float):  # في حالة حدوث خطأ أو استرجاع قيمة افتراضية
        data = {"average_temperature": data}

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"temperature_{timestamp}.json"
    
    try:
        minio_client.put_object(
            Bucket=MINIO_BUCKET_NAME,
            Key=file_name,
            Body=json.dumps(data),
            ContentType="application/json"
        )
        print(f"✅ Data stored in MinIO: {file_name}")
    except Exception as e:
        print(f"❌ Error storing data in MinIO: {e}")

# Auto-save data every 5 minutes
def periodic_store():
    while True:
        store_data_in_minio()
        time.sleep(300)  # كل 5 دقائق

# تشغيل التخزين التلقائي في thread منفصل

threading.Thread(target=periodic_store, daemon=True).start()

@app.route('/temperature', methods=['GET'])
def get_temperature():
    """
    Handles the /temperature endpoint and returns the average temperature with status.
    """
    REQUEST_COUNT.inc()  # Increment request count metric
    data = get_temperature_data()

    # لو رجعلي float ده معناه إن فيه مشكلة، فبرجعه مباشرة بدون أي معالجة
    if isinstance(data, (float, int)):
        TEMPERATURE_GAUGE.set(data)  # Update Prometheus metric
        return jsonify({
            "average_temperature": data,
            "status": determine_status(data)
        })

    # Otherwise, process the data normally
    average_temperature = calculate_average_temperature(data)

    # Handle case where no valid temperature is found
    if average_temperature is None:
        average_temperature = 20.0  # Default value

    TEMPERATURE_GAUGE.set(average_temperature)  # Update Prometheus metric

    return jsonify({
        "average_temperature": average_temperature,
        "status": determine_status(average_temperature)
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """
    Exposes Prometheus metrics.
    """
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/store', methods=['POST'])
def store_data_now():
    """
    API endpoint to manually store temperature data in MinIO.
    """
    store_data_in_minio()
    return jsonify({"message": "Data stored successfully in MinIO!"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)