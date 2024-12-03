import unittest
from appVersion import app
class TestAppVerion(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True    
    
    def test_version(self):
        response = self.app.get('/version')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"Version" : "1.0.0"})
        
    if __name__=='__main__' :
        unittest.main()
