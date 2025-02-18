"""
Flask application to serve temperature data with Prometheus metrics and Valkey caching.
"""

from datetime import datetime, timedelta, timezone
import requests
import json
import redis
from flask import Flask, jsonify
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# OpenSenseMap API URL
SENSEBOX_API_URL = "https://api.opensensemap.org/boxes"

# Connect to Valkey (running in the Kubernetes cluster)
valkey_client = redis.Redis(host="valkey-service", port=6379, decode_responses=True)

# Prometheus Metrics
REQUEST_COUNT = Counter('temperature_requests_total', 'Total number of temperature requests')
TEMPERATURE_GAUGE = Gauge('average_temperature', 'Average temperature over the last hour')

def get_temperature_data():
    """
    Fetches temperature data from the openSenseMap API, with caching in Valkey.
    """
    cache_key = "temperature_data"
    
    # Check if data is in Valkey cache
    cached_data = valkey_client.get(cache_key)
    if cached_data:
        return json.loads(cached_data)  # Return cached data

    # If no data in cache, fetch from API
    response = requests.get(SENSEBOX_API_URL, timeout=30)
    if response.status_code == 200:
        data = response.json()
        valkey_client.setex(cache_key, 300, json.dumps(data))  # Store in Valkey for 300 seconds
        return data
    
    # If there was an error fetching data, store a default value
    default_data = {'temperature': 50.0}
    valkey_client.setex(cache_key, 300, json.dumps(default_data))  # Store default value in Valkey
    return default_data

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

@app.route('/temperature', methods=['GET'])
def get_temperature():
    """
    Handles the /temperature endpoint and returns the average temperature with status.
    """
    REQUEST_COUNT.inc()  # Increment request count metric
    data = get_temperature_data()
    
    average_temperature = calculate_average_temperature(data)
    
    if average_temperature is None:
        # Set the default value 50.0 in Redis if no valid temperature is found
        default_temperature = 50.0
        valkey_client.setex("temperature_data", 300, json.dumps({"temperature": default_temperature}))
        average_temperature = default_temperature  # Use the default value

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
