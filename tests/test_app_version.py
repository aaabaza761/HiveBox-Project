"""Unit tests for the app version endpoint."""

import unittest
from Version.app_version import app


class TestAppVersion(unittest.TestCase):
    """Test cases for the /version endpoint."""

    def setUp(self):
        """Set up the test client for the Flask app."""
        self.app = app.test_client()
        self.app.testing = True

    def test_version(self):
        """Test the /version endpoint for correct response."""
        response = self.app.get('/version')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {"Version": "1.0.0"})


if __name__ == '__main__':
    unittest.main()
