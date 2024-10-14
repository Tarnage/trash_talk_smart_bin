import unittest
import json
from unittest.mock import patch, MagicMock
from your_flask_app import app  
from mqtt_subscriber import decode_payload, is_valid_payload, on_message


class TestMQTTSubscriber(unittest.TestCase):
    
    def test_decode_payload_valid(self):
        valid_payload = {
            "downlink_queued": {
                "frm_payload": "eyJiaW5faWQiOiAiMSIsICJsYXRpdHVkZSI6IDMzLjQ1NzIsICJsb25naXR1ZGUiOiAtMzMuNDU3MiwgImNvbGxlY3Rpb25fZnJlZVVubG9ja2VkX3Blcm1hbWV0ZXIiOiAiMSIsICJ0aWx0X3N0YXR1cyI6ICJJbmFjdGl2ZSIsICJmaWxsIHRhcmVuYXJlcyI6ICJKdXN0ZXJzIGNhbGxlZ3UiLCAiY291bnRyeV9uYW1lIjogIlV5bGl0ZSAtIE51bWJlciIgfQ=="
            }
        }
        
        expected_decoded = {
            "bin_id": "1",
            "latitude": 33.45772,
            "longitude": -33.45772,
            "collection_frequency_per_month": 1,
            "tilt_status": "Inactive"
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
            "fill_level_percentage": 150.0,
            "battery_level_percentage": -10.0,
            "temperature_celsius": 1000.0
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
        
        with app.app_context():  # 添加应用上下文
            mock_query.filter_by.return_value.first.return_value = None
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

        with app.app_context():  # 添加应用上下文
            mock_existing_bin = MagicMock()
            mock_query.filter_by.return_value.first.return_value = mock_existing_bin
            mock_db_session.commit.return_value = None
            
            on_message(None, None, MagicMock(payload=json.dumps(payload).encode('utf-8')))
            self.assertTrue(mock_db_session.commit.called)
            self.assertEqual(mock_existing_bin.fill_level_percentage, 85.0)
            self.assertEqual(mock_existing_bin.temperature_celsius, 22.0)


if __name__ == '__main__':
    unittest.main()
