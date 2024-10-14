import unittest
from unittest.mock import patch, MagicMock
import json
import base64
from mqtt_subscriber import app, SmartBinData, db

class TestMQTTSubscriber(unittest.TestCase):
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

    def test_decode_payload_valid(self):
        """Test decoding a valid payload."""
        payload = {
            'downlink_queued': {
                'frm_payload': base64.b64encode(json.dumps({
                    'bin_id': '12345',
                    'latitude': 12.345678,
                    'longitude': 98.765432,
                    'fill_level_percentage': 50,
                }).encode('utf-8')).decode('utf-8')
            }
        }
        decoded_payload = app.decode_payload(json.dumps(payload))
        self.assertIsNotNone(decoded_payload)
        self.assertEqual(decoded_payload['bin_id'], '12345')

    def test_decode_payload_invalid_json(self):
        """Test decoding an invalid JSON payload."""
        payload = "invalid_json"
        decoded_payload = app.decode_payload(payload)
        self.assertIsNone(decoded_payload)

    def test_is_valid_payload_valid(self):
        """Test the payload validation."""
        payload = {
            'bin_id': '12345',
            'fill_level_percentage': 50,
            'battery_level_percentage': 80,
            'temperature_celsius': 22.5
        }
        self.assertTrue(app.is_valid_payload(payload))

    def test_is_valid_payload_invalid(self):
        """Test the payload validation with invalid data."""
        payload = {
            'bin_id': '',
            'fill_level_percentage': 150,  # Invalid
            'battery_level_percentage': 80,
            'temperature_celsius': 22.5
        }
        self.assertFalse(app.is_valid_payload(payload))

    @patch('mqtt_subscriber.SmartBinData.query')
    def test_on_message_update_existing_bin(self, mock_query):
        """Test updating an existing bin."""
        payload = {
            'bin_id': '12345',
            'fill_level_percentage': 60
        }
        existing_bin_mock = MagicMock()
        existing_bin_mock.fill_level_percentage = 50
        mock_query.filter_by.return_value.first.return_value = existing_bin_mock

        with patch('mqtt_subscriber.db.session.commit') as mock_commit:
            app.on_message(None, None, MagicMock(payload=json.dumps(payload).encode('utf-8')))
            self.assertEqual(existing_bin_mock.fill_level_percentage, 60)
            mock_commit.assert_called_once()

    @patch('mqtt_subscriber.SmartBinData.query')
    def test_on_message_create_new_bin(self, mock_query):
        """Test creating a new bin."""
        payload = {
            'bin_id': '67890',
            'fill_level_percentage': 40
        }
        mock_query.filter_by.return_value.first.return_value = None  # No existing bin

        with patch('mqtt_subscriber.db.session.add') as mock_add:
            with patch('mqtt_subscriber.db.session.commit') as mock_commit:
                app.on_message(None, None, MagicMock(payload=json.dumps(payload).encode('utf-8')))
                mock_add.assert_called_once()
                mock_commit.assert_called_once()

if __name__ == '__main__':
    unittest.main()
