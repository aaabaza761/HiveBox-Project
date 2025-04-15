from flask import Flask, jsonify,Response
import requests
from datetime import datetime, timedelta, timezone
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST,Histogram
import time
import redis,boto3
import os
import threading,json




app = Flask(__name__)


# ================== Prometheus Metrics ==================
# عدد الطلبات لكل endpoint
REQUEST_COUNTER = Counter(
    'flask_app_requests_total',
    'Total number of requests',
    ['method', 'endpoint']
)

# وقت الاستجابة لكل endpoint
REQUEST_LATENCY = Histogram(
    'flask_app_request_latency_seconds',
    'Latency of requests in seconds',
    ['method', 'endpoint']
)

CACHE_HIT_RATIO = Gauge('cache_hit_ratio', 'Ratio of cache hits to total requests')
STORE_REQUESTS_TOTAL = Counter('store_requests_total', 'Total number of store requests')



# ================== connect the valkey(cashe layer) ======

valkey_client=redis.Redis(host="valkey-service", port=6379, decode_responses=True)


# MinIO Configuration

MINIO_ACCESS_KEY = "admin"
MINIO_SECRET_KEY = "password"
MINIO_ENDPOINT = "http://minio-service:9000"
MINIO_BUCKET_NAME = "hivebox-storage"

# ================== connect the minIO(Storage layer) ======

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

# ================== Utility Functions ====================

def build_urls_from_ids(boxes_id):
    return [f"https://api.opensensemap.org/boxes/{box_id}?format=json" for box_id in boxes_id]

def fetch_box_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

def extract_temperature_from_box(data):
    if not data:
        return None
    
    now = datetime.now(timezone.utc)
    one_hour_ago = now -  timedelta(hours=1)

    for sensor in data.get("sensors", []):
        if sensor.get("title").lower() == "temperature" or sensor.get("title").lower() == "temperatur" :
            last = sensor.get("lastMeasurement")
            if last:
                try:
                    created_at = datetime.fromisoformat(last["createdAt"].replace("Z", "+00:00"))
                    if created_at >= one_hour_ago:
                        return float(last["value"])
                except Exception:
                    return None
    return None

def get_temperature_last_hour():
    boxes_id =["5d8b36c15f3de0001abe60ea",
                "5d653fe8953683001a901323",
                "66506c7d96a6830008c33955",
                "67371eb8a5dfb4000700bda3"]

    urls = build_urls_from_ids(boxes_id)
    temperatures = []

    for url in urls:
        box_data = fetch_box_data(url)
        temp = extract_temperature_from_box(box_data)
        if temp is not None:
            temperatures.append(temp)

    return temperatures

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
    STORE_REQUESTS_TOTAL.inc()  # Increment store requests metric
    temps = get_temperature_last_hour()
    average = sum(temps) / len(temps)
    status=determine_status(average)
    data = {
        "Average": average,
        "status": status
    }
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
    


# Cache hit/miss tracking
cache_hits = 0
cache_misses = 0

# ================== Flask Route ===================

@app.route("/temperature", methods=["GET"])
def get_average_temperature():
    global cache_hits, cache_misses  # Declare the variables as global
    
    start_time = time.time()
    REQUEST_COUNTER.labels(method='GET', endpoint='/temperature/average').inc()
    #return data from cash
    cache_key = "average_temperature"
    cached_data = valkey_client.get(cache_key)
    if cached_data:
        cache_hits+=1
        CACHE_HIT_RATIO.set(cache_hits / (cache_hits + cache_misses))  # Update cache hit ratio
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method='GET', endpoint='/temperature/average').observe(latency)
        average = float(cached_data)
        status = determine_status(average)
        return jsonify({
            "Average": round(average, 2),
            "Status": status,
            "source": "cache"
        }), 200
    
    # If no data in cache, fetch from API
    cache_misses += 1
    temps = get_temperature_last_hour()
    if not temps:
        latency = time.time() - start_time
        REQUEST_LATENCY.labels(method='GET', endpoint='/temperature/average').observe(latency)
        return jsonify({
            "message": "No temperature data found in the last hour.",
            "temperatures": [],
            "average": None
        }), 200
    
    average = sum(temps) / len(temps)
    status=determine_status(average)
    latency = time.time() - start_time
    REQUEST_LATENCY.labels(method='GET', endpoint='/temperature/average').observe(latency)
    CACHE_HIT_RATIO.set(cache_hits / (cache_hits + cache_misses))  # Update cache hit ratio
         
    # store in cash for 5 minutes(300 sec)
    valkey_client.setex(cache_key, 300, str(average))
    valkey_client.set("temperature_cache_timestamp", time.time())  # Store cache timestamp
    
    return jsonify({
        "Average": round(average, 2),
        "Status": status,
        "source": "live"
        }), 200

@app.route("/metrics")
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)

@app.route('/store', methods=['POST'])
def store_data_now():
    """
    API endpoint to manually store temperature data in MinIO.
    """
    store_data_in_minio()
    return jsonify({"message": "Data stored successfully in MinIO!"}), 200

# ================== /readyz Endpoint ===================
@app.route("/readyz", methods=["GET"])
def readyz():
    # Check if the senseBoxes are accessible
    boxes_id =["5d8b36c15f3de0001abe60ea",
                "5d653fe8953683001a901323",
                "66506c7d96a6830008c33955",
                "67371eb8a5dfb4000700bda3"]
    accessible_boxes = 0
    try:
        for box_id in boxes_id:
            url = f"https://api.opensensemap.org/boxes/{box_id}?format=json"
            if fetch_box_data(url):
                accessible_boxes += 1

        # Check if 50% + 1 of the senseBoxes are accessible
        if accessible_boxes < (len(boxes_id) // 2) + 1:
            return jsonify({"status": "unhealthy", "reason": "Not enough senseBoxes accessible"}), 503
        cache_timestamp = valkey_client.get("temperature_cache_timestamp")
        if not cache_timestamp or (datetime.now(timezone.utc) - datetime.fromtimestamp(float(cache_timestamp), timezone.utc)) > timedelta(minutes=5):
            return Response("Cache is outdated!", status=503)

        return Response("OK", status=200)

    except Exception as e:
        return Response(f"Error checking readiness: {str(e)}", status=503)


# ================== Run App ===================

if __name__ == "__main__":
    app.run(debug=True,host="0.0.0.0",port=5000)
