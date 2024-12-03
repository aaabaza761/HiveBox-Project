import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from Temp.appTemp import calculate_average_temperature, get_temperature_data, app

class TestTemperatureAPI(unittest.TestCase):

    @patch('Temp.appTemp.requests.get')
    def test_get_temperature_data_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "test"}]
        mock_get.return_value = mock_response

        data = get_temperature_data()
        self.assertEqual(data, [{"id": "test"}])

    @patch('Temp.appTemp.requests.get')
    def test_get_temperature_data_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        data = get_temperature_data()
        self.assertEqual(data, [])

    def test_calculate_average_temperature(self):
        now = datetime.now(timezone.utc)
        data = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (now - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        "lastMeasurement": "22.5",
                    },
                    {
                        "_id": "sensor2",
                        "title": "Temperatur",
                        "lastMeasurementAt": (now - timedelta(minutes=90)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        "lastMeasurement": "20.0",
                    },
                ]
            }
        ]
        average_temp = calculate_average_temperature(data)
        self.assertAlmostEqual(average_temp, 22.5)

    def test_calculate_average_temperature_no_recent_data(self):
        now = datetime.now(timezone.utc)
        data = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        "lastMeasurement": "22.5",
                    }
                ]
            }
        ]
        average_temp = calculate_average_temperature(data)
        self.assertIsNone(average_temp)

    def test_calculate_average_temperature_missing_id(self):
        now = datetime.now(timezone.utc)
        data = [
            {
                "sensors": [
                    {
                        "title": "Temperatur",
                        "lastMeasurementAt": (now - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        "lastMeasurement": "22.5",
                    }
                ]
            }
        ]
        average_temp = calculate_average_temperature(data)
        self.assertAlmostEqual(average_temp, 22.5)

    @patch('Temp.appTemp.get_temperature_data')
    def test_get_temperature_endpoint_success(self, mock_get_temperature_data):
        now = datetime.now(timezone.utc)
        mock_get_temperature_data.return_value = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (now - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        "lastMeasurement": "22.5",
                    }
                ]
            }
        ]
        with app.test_client() as client:
            response = client.get('/temp')
            self.assertEqual(response.status_code, 200)
            self.assertIn("average_temperature", response.get_json())

    @patch('Temp.appTemp.get_temperature_data')
    def test_get_temperature_endpoint_no_data(self, mock_get_temperature_data):
        mock_get_temperature_data.return_value = []
        with app.test_client() as client:
            response = client.get('/temp')
            self.assertEqual(response.status_code, 500)
            self.assertIn("error", response.get_json())

    @patch('Temp.appTemp.get_temperature_data')
    def test_get_temperature_endpoint_no_valid_data(self, mock_get_temperature_data):
        now = datetime.now(timezone.utc)
        mock_get_temperature_data.return_value = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                        "lastMeasurement": "22.5",
                    }
                ]
            }
        ]
        with app.test_client() as client:
            response = client.get('/temp')
            self.assertEqual(response.status_code, 404)
            self.assertIn("error", response.get_json())

if __name__ == '__main__':
    unittest.main()
