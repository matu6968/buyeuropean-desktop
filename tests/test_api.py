"""Tests for the API module."""

import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json

from buyeuropean.api import BuyEuropeanAPI


class TestBuyEuropeanAPI(unittest.TestCase):
    """Test cases for the BuyEuropeanAPI class."""

    def setUp(self):
        """Set up test fixtures."""
        self.api = BuyEuropeanAPI()

    @patch('buyeuropean.api.requests.get')
    def test_get_location_data(self, mock_get):
        """Test getting location data."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "city": "Berlin",
            "country_name": "Germany",
            "country_code": "DE"
        }
        mock_get.return_value = mock_response

        # Call the method
        result = self.api.get_location_data()

        # Check the result
        self.assertEqual(result["city"], "Berlin")
        self.assertEqual(result["country"], "Germany")
        self.assertEqual(result["country_code"], "DE")

    @patch('buyeuropean.api.requests.post')
    @patch('buyeuropean.api.BuyEuropeanAPI.get_location_data')
    @patch('buyeuropean.api.BuyEuropeanAPI.image_to_base64')
    def test_analyze_product(
        self, mock_to_base64, mock_get_location, mock_post
    ):
        """Test analyzing a product."""
        # Create mock data
        mock_to_base64.return_value = "base64_image_data"
        mock_get_location.return_value = {
            "city": "Berlin",
            "country": "Germany",
            "country_code": "DE"
        }

        # Create a mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "identified_product_name": "Test Product",
            "identified_company": "Test Company",
            "identified_headquarters": "United States",
            "classification": "european_sceptic"
        }
        mock_post.return_value = mock_response

        # Call the method
        result = self.api.analyze_product(Path("test_image.jpg"))

        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result["identified_product_name"], "Test Product")
        self.assertEqual(result["identified_company"], "Test Company")
        self.assertEqual(result["classification"], "european_sceptic")

        # Verify the API was called with the correct data
        expected_payload = {
            "image": "base64_image_data",
            "userLocation": {
                "city": "Berlin",
                "country": "Germany",
                "country_code": "DE"
            }
        }

        # Verify post was called with the correct arguments
        _, kwargs = mock_post.call_args
        actual_payload = json.loads(kwargs["data"])
        self.assertEqual(actual_payload, expected_payload)


if __name__ == '__main__':
    unittest.main()
