import unittest
from app import app, db, SmartBinData

class TestFlaskApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the test client and create the database."""
        cls.app = app.test_client()
        cls.app_context = app.app_context()
        cls.app_context.push()
        db.create_all()

    @classmethod
    def tearDownClass(cls):
        """Drop the database after tests."""
        db.session.remove()
        db.drop_all()
        cls.app_context.pop()

    def test_index_route(self):
        """Test the index route."""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SmartBin Flask App is running!', response.data)

if __name__ == '__main__':
    unittest.main()
