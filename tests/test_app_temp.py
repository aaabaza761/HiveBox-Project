import unittest
from unittest.mock import patch
from Temp.app_temp import get_temperature_last_hour, determine_status


class TestHiveBoxApp(unittest.TestCase):

    @patch('Temp.app_temp.fetch_box_data')  # Mocking fetch_box_data function
    def test_get_temperature_last_hour(self, mock_fetch):
        # Mocking response from fetch_box_data
        mock_fetch.return_value = {
            "sensors": [
                {
                    "title": "Temperature",
                    "lastMeasurement": {
                        "value": "25.5",
                        "createdAt": "2025-04-16T12:00:00Z"
                    }
                }
            ]
        }

        # Call the function
        temperatures = get_temperature_last_hour()

        # Assert that the temperatures list is not empty and contains the mocked value
        self.assertGreater(len(temperatures), 0)
        self.assertEqual(temperatures[0], 25.5)

    def test_determine_status(self):
        # Test for "Too Cold"
        self.assertEqual(determine_status(5), "Too Cold")
        
        # Test for "Good"
        self.assertEqual(determine_status(20), "Good")
        
        # Test for "Too Hot"
        self.assertEqual(determine_status(40), "Too Hot")


if __name__ == "__main__":
    unittest.main()
