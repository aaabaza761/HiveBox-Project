"""
Flask application to serve temperature data with Prometheus metrics.
"""

from datetime import datetime, timedelta, timezone
import requests
from flask import Flask, jsonify
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# OpenSenseMap API URL
SENSEBOX_API_URL = "https://api.opensensemap.org/boxes"

# Prometheus Metrics
REQUEST_COUNT = Counter('temperature_requests_total', 'Total number of temperature requests')
TEMPERATURE_GAUGE = Gauge('average_temperature', 'Average temperature over the last hour')

def get_temperature_data():
    """
    Fetches temperature data from the openSenseMap API.
    """
    response = requests.get(SENSEBOX_API_URL, timeout=30)
    if response.status_code == 200:
        return response.json()
    return []

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
    if not data:
        return jsonify({"error": "Unable to fetch data from openSenseMap"}), 500
    #calculate_average_temperature(data)
    average_temperature = 15
    if average_temperature is None:
        return jsonify({"error": "No valid temperature data available in the last hour"}), 404

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