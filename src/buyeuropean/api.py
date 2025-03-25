"""API client for BuyEuropean service."""

import base64
import json
import requests
import platform
import io
from typing import Dict, Any, Optional, Tuple, List, Union, Literal
from pathlib import Path
from PIL import Image

VERSION = "1.0.0"
API_ENDPOINT = "https://buy-e-ubackend-felixgraeber.replit.app/analyze-product"
FEEDBACK_ENDPOINT = "https://buy-e-ubackend-felixgraeber.replit.app/api/feedback/analysis"

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
        
        # Store the most recent analysis ID for feedback
        self.last_analysis_id = None
    
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
                
                # Store the analysis ID for potential feedback
                if "id" in result:
                    self.last_analysis_id = result["id"]
                
                # Map classification values if needed for compatibility
                # The API uses values like 'european_sceptic', 'european_country', 'european_ally'
                classification = result.get("classification")
                if classification == "european":
                    # Handle older API responses that might use 'european'
                    result["classification"] = "european_country"
                    
                # Normalize alternative names to lowercase to handle inconsistent API responses
                if "alternatives" in result and result["alternatives"]:
                    normalized_alternatives = []
                    for alt in result["alternatives"]:
                        if "name" in alt and alt["name"]:
                            # Ensure first letter is capitalized for display
                            alt["name"] = alt["name"].capitalize()
                        normalized_alternatives.append(alt)
                    result["alternatives"] = normalized_alternatives
                
                return result
            else:
                print(f"API error: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            print(f"Error analyzing product: {e}")
            return None
    
    def send_feedback(self, 
                     is_positive: bool,
                     wrong_product: bool = False,
                     wrong_brand: bool = False,
                     wrong_country: bool = False,
                     wrong_classification: bool = False,
                     wrong_alternatives: bool = False,
                     wrong_other: bool = False,
                     feedback_text: str = "") -> Dict[str, Any]:
        """Send feedback about an analysis to the API.
        
        Args:
            is_positive: True if feedback is positive (thumbs up), False if negative (thumbs down)
            wrong_product: True if product identification was incorrect
            wrong_brand: True if brand identification was incorrect
            wrong_country: True if country identification was incorrect
            wrong_classification: True if classification was incorrect
            wrong_alternatives: True if suggested alternatives were incorrect
            wrong_other: True if there was another issue
            feedback_text: Additional text feedback
            
        Returns:
            API response as a dictionary
        """
        if not self.last_analysis_id:
            return {"status": "error", "message": "No analysis ID available for feedback"}
        
        payload = {
            "analysis_id": self.last_analysis_id,
            "is_positive": is_positive,
            "wrong_product": wrong_product,
            "wrong_brand": wrong_brand,
            "wrong_country": wrong_country,
            "wrong_classification": wrong_classification,
            "wrong_alternatives": wrong_alternatives,
            "wrong_other": wrong_other,
            "feedback_text": feedback_text
        }
        
        try:
            response = requests.post(
                FEEDBACK_ENDPOINT,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Feedback API error: {response.status_code}, {response.text}")
                return {"status": "error", "message": f"API error: {response.status_code}"}
                
        except Exception as e:
            print(f"Error sending feedback: {e}")
            return {"status": "error", "message": str(e)} 