import unittest
from Temp.app_temp import app
import time

class TestPerformance(unittest.TestCase):

    def test_temperature_endpoint_performance(self):
        with app.test_client() as client:
            start_time = time.time()
            response = client.get('/temperature')
            end_time = time.time()
            self.assertLess(end_time - start_time, 1)  # اختبار أنه لا يستغرق أكثر من ثانية

if __name__ == '__main__':
    unittest.main(