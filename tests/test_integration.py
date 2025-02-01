import unittest
from unittest.mock import patch
from Temp.app_temp import app

class TestTemperatureAPIIntegration(unittest.TestCase):

    @patch('Temp.app_temp.get_temperature_data')
    def test_get_temperature_endpoint(self, mock_get_temperature_data):
        mock_get_temperature_data.return_value = [{"sensors": [{"title": "Temperatur", "lastMeasurement": "22.5"}]}]
        with app.test_client() as client:
            response = client.get('/temperature')
            self.assertEqual(response.status_code, 200)
            self.assertIn("average_temperature", response.get_json())

if __name__ == '__main__':
    unittest.main()
