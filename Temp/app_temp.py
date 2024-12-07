"""
This module defines a Flask application that serves the average temperature from the last hour.
"""

from datetime import datetime, timedelta, timezone
import requests
from flask import Flask, jsonify

app = Flask(__name__)

# openSenseMap API URL
SENSEBOX_API_URL = "https://api.opensensemap.org/boxes"

def get_temperature_data():
    """
    Fetches temperature data from the openSenseMap API.
    Returns:
        list: A list of senseBox data if the API call is successful, otherwise an empty list.
    """
    response = requests.get(SENSEBOX_API_URL, timeout=10)
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
                print(f"No lastMeasurementAt for sensor {sensor.get('_id', 'unknown')}")
                continue

            try:
                last_measurement_time = datetime.strptime(
                    last_measurement_at, '%Y-%m-%dT%H:%M:%S.%fZ'
                ).replace(tzinfo=timezone.utc)
            except ValueError as e:
                print(f"Error parsing lastMeasurementAt: {e}")
                continue

            if now - last_measurement_time > timedelta(hours=1):
                print(
                    f"Skipping sensor {sensor.get('_id', 'unknown')} - "
                    "Measurement older than 1 hour."
                )

                continue

            temperature = sensor.get('lastMeasurement')
            if temperature:
                valid_temperatures.append(float(temperature))

    if valid_temperatures:
        return sum(valid_temperatures) / len(valid_temperatures)
    return None

@app.route('/temp', methods=['GET'])
def get_temperature():
    """
    Handles the /temp endpoint and returns the average temperature for the last hour.
    """
    data = get_temperature_data()
    if not data:
        return jsonify({"error": "Unable to fetch data from openSenseMap"}), 500
    average_temperature = calculate_average_temperature(data)
    if average_temperature is None:
        return jsonify({"error": "No valid temperature data available in the last hour"}), 404

    return jsonify({"average_temperature": average_temperature})

if __name__ == '__main__':
    app.run(debug=True)
