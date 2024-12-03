import requests
from flask import Flask, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# openSenseMap API URL
SENSEBOX_API_URL = "https://api.opensensemap.org/boxes"

# Function to fetch temperature data from the openSenseMap API
def get_temperature_data():
    response = requests.get(SENSEBOX_API_URL)
    if response.status_code == 200:
        return response.json()
    return []

# Function to filter and calculate the average temperature
def calculate_average_temperature(data):
    now = datetime.utcnow()
    valid_temperatures = []

    for box in data:
        # Loop through each sensor to find temperature readings
        for sensor in box.get('sensors', []):
            # Check if 'title' exists in the sensor and if it matches 'Temperatur'
            if 'title' in sensor and sensor['title'] == 'Temperatur':
                # Get the timestamp of the last measurement
                last_measurement_at = sensor.get('lastMeasurementAt')
                if last_measurement_at:
                    try:
                        last_measurement_time = datetime.strptime(last_measurement_at, '%Y-%m-%dT%H:%M:%S.%fZ')
                    except Exception as e:
                        print(f"Error parsing lastMeasurementAt: {e}")
                        continue
                    
                    # If the measurement is within the last 1 hour, consider it
                    if now - last_measurement_time <= timedelta(hours=1):
                        # We assume the temperature value is stored in 'lastMeasurement' for this example
                        # Adjust based on actual response or API
                        temperature = sensor.get('lastMeasurement')  # Replace this if temperature is in another field
                        if temperature:
                            valid_temperatures.append(float(temperature))  # Convert to float for averaging
                        else:
                            print(f"Missing temperature value for sensor {sensor['_id']}")
                    else:
                        print(f"Skipping sensor {sensor['_id']} - Measurement older than 1 hour.")
                else:
                    print(f"No lastMeasurementAt for sensor {sensor['_id']}")
    
    # Log the number of valid temperatures found
    print(f"Found {len(valid_temperatures)} valid temperature readings in the last hour.")
    #return data 
    # Calculate the average temperature
    if valid_temperatures:
        return sum(valid_temperatures) / len(valid_temperatures)
    return None

# Route to get the current average temperature
@app.route('/temp', methods=['GET'])
def get_temperature():
    data = get_temperature_data()
    if not data:
        return jsonify({"error": "Unable to fetch data from openSenseMap"}), 500
    
    average_temperature = calculate_average_temperature(data)
    if average_temperature is None:
        return jsonify({"error": "No valid temperature data available in the last hour"}), 404
    
    return jsonify({"average_temperature": average_temperature})

if __name__ == '__main__':
    app.run(debug=True)
