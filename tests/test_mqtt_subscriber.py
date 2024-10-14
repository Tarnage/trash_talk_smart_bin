import unittest
import json
from unittest.mock import patch, MagicMock
from app import app, db, SmartBinData  # Ensure this matches your actual Flask app module
from mqtt_subscriber import decode_payload, is_valid_payload, on_message

class TestMQTTSubscriber(unittest.TestCase):

    def test_decode_payload_valid(self):
        valid_payload = {
            "downlink_queued": {
                "frm_payload": "eyJiaW5faWQiOiAiYmluMTIzIiwgImZpbGxfbGV2ZWxfcGVyY2VudGFnZSI6ICIxNSIsICJiYXR0ZXJ5X2xldmVsX3BlcmNlbnRhZ2UiOiAiODAiLCAidGVtcGVyYXR1cmVfY2Vsc2l1cyI6ICIzMCJ9"
            }
        }
        
        expected_decoded = {
            "bin_id": "bin123",
            "fill_level_percentage": 15.0,
            "battery_level_percentage": 80.0,
            "temperature_celsius": 30.0
        }
        
        decoded_payload = decode_payload(json.dumps(valid_payload))
        self.assertEqual(decoded_payload, expected_decoded)

    def test_decode_payload_invalid_json(self):
        invalid_payload = "invalid json"
        decoded_payload = decode_payload(invalid_payload)
        self.assertIsNone(decoded_payload)

    def test_is_valid_payload_valid(self):
        valid_payload = {
            "bin_id": "1",
            "fill_level_percentage": 50.0,
            "battery_level_percentage": 80.0,
            "temperature_celsius": 25.0
        }
        is_valid = is_valid_payload(valid_payload)
        self.assertTrue(is_valid)

    def test_is_valid_payload_invalid(self):
        invalid_payload = {
            "bin_id": "",
            "fill_level_percentage": 150.0,  # Invalid fill level
            "battery_level_percentage": -10.0,  # Invalid battery level
            "temperature_celsius": 1000.0  # Invalid temperature
        }
        is_valid = is_valid_payload(invalid_payload)
        self.assertFalse(is_valid)

    @patch('mqtt_subscriber.db.session')
    @patch('mqtt_subscriber.SmartBinData.query')
    def test_on_message_create_new_bin(self, mock_query, mock_db_session):
        payload = {
            "bin_id": "2",
            "latitude": 33.45772,
            "longitude": -33.45772,
            "collection_frequency_per_month": 1,
            "average_collection_time_days": 5,
            "tilt_status": "Active",
            "fill_level_percentage": 75.0,
            "temperature_celsius": 20.0,
            "displacement": "None",
            "days_since_last_emptied": 2,
            "communication_status": "Online",
            "battery_level_percentage": 90.0
        }
        
        with app.app_context():  # Ensure Flask app context is active
            mock_query.filter_by.return_value.first.return_value = None  # No existing bin
            mock_db_session.commit.return_value = None
            
            on_message(None, None, MagicMock(payload=json.dumps(payload).encode('utf-8')))
            self.assertTrue(mock_db_session.add.called)

    @patch('mqtt_subscriber.db.session')
    @patch('mqtt_subscriber.SmartBinData.query')
    def test_on_message_update_existing_bin(self, mock_query, mock_db_session):
        payload = {
            "bin_id": "1",
            "fill_level_percentage": 85.0,
            "temperature_celsius": 22.0
        }

        with app.app_context():  # Ensure Flask app context is active
            mock_existing_bin = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_existing_bin  # Mock existing bin
            mock_db_session.commit.return_value = None
            
            on_message(None, None, MagicMock(payload=json.dumps(payload).encode('utf-8')))
            self.assertTrue(mock_db_session.commit.called)
            self.assertEqual(mock_existing_bin.fill_level_percentage, 85.0)
            self.assertEqual(mock_existing_bin.temperature_celsius, 22.0)

    def test_decode_payload_error_handling(self):
        """Test decode_payload for error handling with invalid Base64."""
        invalid_payload = json.dumps({
            "downlink_queued": {"frm_payload": "invalid_base64"}
        })

        result = decode_payload(invalid_payload)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
