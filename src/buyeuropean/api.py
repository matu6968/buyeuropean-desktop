"""API client for BuyEuropean service."""

import base64
import json
import requests
import platform
import io
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from PIL import Image

VERSION = "1.0.0"
API_ENDPOINT = "https://buy-e-ubackend-felixgraeber.replit.app/analyze-product"

class BuyEuropeanAPI:
    """Client for the BuyEuropean API."""
    
    def __init__(self):
        """Initialize the API client."""
        # Generate custom user agent and corresponding headers
        user_agent, sec_headers = self._get_browser_headers()
        
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://buyeuropean.io',
            'priority': 'u=1, i',
            'referer': 'https://buyeuropean.io/',
            'sec-ch-ua': sec_headers['sec-ch-ua'],
            'sec-ch-ua-mobile': sec_headers['sec-ch-ua-mobile'],
            'sec-ch-ua-platform': sec_headers['sec-ch-ua-platform'],
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': user_agent
        }
    
    def _get_browser_headers(self) -> Tuple[str, Dict[str, str]]:
        """Get a custom user agent string and corresponding sec-ch headers.
        
        Returns:
            A tuple of (user_agent, sec_headers_dict)
        """
        # Get platform name in a readable format
        system_platform = platform.system()
        if system_platform == "Darwin":
            system_platform = "macOS"
        
        # Create custom user agent in the format "BuyEuropean Desktop Client (Platform) Version"
        user_agent = f"BuyEuropean Desktop Client ({system_platform}) {VERSION}"
        
        # Set simple sec headers based on platform
        sec_headers = {
            'sec-ch-ua': '"BuyEuropean Desktop";v="1"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': f'"{system_platform}"',
        }
        
        return user_agent, sec_headers
    
    def get_location_data(self) -> Dict[str, str]:
        """Get user location data from ipapi.co."""
        try:
            response = requests.get("https://ipapi.co/json/")
            data = response.json()
            return {
                "city": data.get("city", "Unknown"),
                "country": data.get("country_name", "Unknown"),
                "country_code": data.get("country_code", "XX")
            }
        except Exception as e:
            print(f"Error getting location data: {e}")
            return {
                "city": "Unknown",
                "country": "Unknown",
                "country_code": "XX"
            }
    
    def image_to_base64(self, image_path: Path) -> str:
        """Convert an image file to base64 encoded string.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded JPEG image data as a string
            
        Notes:
            This method automatically converts/remuxes any image format to JPEG
            to ensure compatibility with the API server.
        """
        try:
            # Open and convert the image using Pillow
            with Image.open(image_path) as img:
                # Convert to RGB if it has an alpha channel (like PNG)
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    # Create a white background image
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    # Paste the image on the background if it has alpha
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                    else:
                        background.paste(img)
                    img = background
                elif img.mode != 'RGB':
                    # Convert other modes to RGB
                    img = img.convert('RGB')
                
                # Save as JPEG to an in-memory file
                buffer = io.BytesIO()
                img.save(buffer, format='JPEG', quality=90)
                buffer.seek(0)
                
                # Convert to base64
                return base64.b64encode(buffer.read()).decode('utf-8')
                
        except Exception as e:
            print(f"Error processing image: {e}")
            # If conversion fails, try the original method as fallback
            try:
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
            except Exception as e2:
                print(f"Failed to read original image: {e2}")
                raise ValueError(f"Could not process image at {image_path}: {e}") from e
    
    def analyze_product(self, image_path: Path) -> Optional[Dict[str, Any]]:
        """Send a product image to the API for analysis."""
        try:
            # Get user location
            user_location = self.get_location_data()
            
            # Convert image to base64 (now with automatic conversion to JPEG)
            image_base64 = self.image_to_base64(image_path)
            
            # Prepare the payload
            payload = {
                "image": image_base64,
                "userLocation": user_location
            }
            
            # Make the API request
            response = requests.post(
                API_ENDPOINT,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                
                # Map classification values if needed for compatibility
                # The API uses values like 'european_sceptic', 'european_country', 'european_ally'
                classification = result.get("classification")
                if classification == "european":
                    # Handle older API responses that might use 'european'
                    result["classification"] = "european_country"
                
                return result
            else:
                print(f"API error: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            print(f"Error analyzing product: {e}")
            return None 