"""
Unit tests for the app_temp Flask application.
Tests the functionality of temperature data processing and API endpoints.
"""

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone
from Temp.app_temp import calculate_average_temperature, get_temperature_data, app


class TestTemperatureAPI(unittest.TestCase):
    """Unit tests for temperature-related functionality in the app_temp module."""

    @patch('Temp.app_temp.requests.get')
    def test_get_temperature_data_success(self, mock_get):
        """
        Test successful data retrieval from the openSenseMap API.
        Mock the API response to ensure correct handling of valid data.
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "test"}]
        mock_get.return_value = mock_response

        data = get_temperature_data()
        self.assertEqual(data, [{"id": "test"}])

    @patch('Temp.app_temp.requests.get')
    def test_get_temperature_data_failure(self, mock_get):
        """
        Test failed data retrieval from the openSenseMap API.
        Mock the API response to simulate an error status code.
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        data = get_temperature_data()
        self.assertEqual(data, [])

    def test_calculate_average_temperature(self):
        """
        Test calculating the average temperature with valid data.
        Ensure only data within the last hour is considered.
        """
        now = datetime.now(timezone.utc)
        data = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (
                                    now - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'
                                            ),
                        "lastMeasurement": "22.5",
                    },
                    {
                        "_id": "sensor2",
                        "title": "Temperatur",
                        "lastMeasurementAt": (
                            now - timedelta(minutes=90)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'
                                            ),
                        "lastMeasurement": "20.0",
                    },
                ]
            }
        ]
        average_temp = calculate_average_temperature(data)
        self.assertAlmostEqual(average_temp, 22.5)

    def test_calculate_average_temperature_no_recent_data(self):
        """
        Test calculating the average temperature with no recent data.
        Ensure data older than one hour is excluded.
        """
        now = datetime.now(timezone.utc)
        data = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (
                            now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'
                                            ),
                        "lastMeasurement": "22.5",
                    }
                ]
            }
        ]
        average_temp = calculate_average_temperature(data)
        self.assertIsNone(average_temp)

    @patch('Temp.app_temp.get_temperature_data')
    def test_get_temperature_endpoint_success(self, mock_get_temperature_data):
        """
        Test the /temp endpoint with valid temperature data.
        Mock the temperature data retrieval to simulate valid data.
        """
        now = datetime.now(timezone.utc)
        mock_get_temperature_data.return_value = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (
                            now - timedelta(minutes=30)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'
                                            ),
                        "lastMeasurement": "22.5",
                    }
                ]
            }
        ]
        with app.test_client() as client:
            response = client.get('/temp')
            self.assertEqual(response.status_code, 200)
            self.assertIn("average_temperature", response.get_json())

    @patch('Temp.app_temp.get_temperature_data')
    def test_get_temperature_endpoint_no_data(self, mock_get_temperature_data):
        """
        Test the /temp endpoint with no data returned.
        Mock the temperature data retrieval to simulate an empty dataset.
        """
        mock_get_temperature_data.return_value = []
        with app.test_client() as client:
            response = client.get('/temp')
            self.assertEqual(response.status_code, 500)
            self.assertIn("error", response.get_json())

    @patch('Temp.app_temp.get_temperature_data')
    def test_get_temperature_endpoint_no_valid_data(self, mock_get_temperature_data):
        """
        Test the /temp endpoint with no valid temperature data.
        Mock the temperature data retrieval to simulate invalid or outdated data.
        """
        now = datetime.now(timezone.utc)
        mock_get_temperature_data.return_value = [
            {
                "sensors": [
                    {
                        "_id": "sensor1",
                        "title": "Temperatur",
                        "lastMeasurementAt": (
                            now - timedelta(hours=2)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'
                                                               ),
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
