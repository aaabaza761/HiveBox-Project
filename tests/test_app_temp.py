import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# ———————————— Mock MinIO client ————————————
import boto3
boto3.client = MagicMock(
    return_value=MagicMock(
        head_bucket=MagicMock(return_value=None),
        create_bucket=MagicMock(return_value=None),
        put_object=MagicMock(return_value=None)
    )
)

# ———————————— Mock Redis client ————————————
import redis
redis.Redis = MagicMock(
    return_value=MagicMock(
        get=MagicMock(return_value=None),
        setex=MagicMock(return_value=None),
        set=MagicMock(return_value=None)
    )
)

# بعد الموكات، نستورد الدوال اللي بنختبرها
from Temp.app_temp import get_temperature_last_hour, determine_status

class TestHiveBoxApp(unittest.TestCase):

    @patch('Temp.app_temp.fetch_box_data')
    def test_get_temperature_last_hour(self, mock_fetch):
        # Timestamp داخل آخر ساعة
        now = datetime.now(timezone.utc)
        iso_now = now.isoformat().replace('+00:00', 'Z')

        mock_fetch.return_value = {
            "sensors": [
                {
                    "title": "Temperature",
                    "lastMeasurement": {
                        "value": "25.5",
                        "createdAt": iso_now
                    }
                }
            ]
        }

        temps = get_temperature_last_hour()
        # نتوقع أربع قيم لأن القائمة تحتوي على 4 box IDs
        self.assertEqual(len(temps), 4)
        for temp in temps:
            self.assertEqual(temp, 25.5)

    def test_determine_status(self):
        self.assertEqual(determine_status(5), "Too Cold")
        self.assertEqual(determine_status(20), "Good")
        self.assertEqual(determine_status(40), "Too Hot")

if __name__ == "__main__":
    unittest.main()
