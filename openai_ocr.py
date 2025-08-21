"""
Universal document processor for all carbon footprint-related paper documents
"""

import base64
import io
import json
import requests
from typing import Dict, List, Optional
from PIL import Image
import os

# Import config for Azure OpenAI
try:
    from config import get_azure_openai_config, is_azure_openai
    AZURE_CONFIG_AVAILABLE = True
    print("✅ Azure OpenAI configuration imported successfully")
except ImportError as e:
    print(f"❌ Azure OpenAI config not available: {e}")
    AZURE_CONFIG_AVAILABLE = False

class OpenAIOCR:
    """
    Azure OpenAI GPT-4 Vision OCR processor for all carbon footprint documents
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Azure OpenAI OCR processor
        
        Args:
            api_key: API key (optional, will use config if not provided)
        """
        if not AZURE_CONFIG_AVAILABLE:
            self.client = None
            self.config = None
            print("⚠️ Azure OpenAI configuration not available")
            return
            
        try:
            # Get Azure OpenAI configuration
            self.config = get_azure_openai_config()
            self.api_key = api_key or self.config["api_key"]
            
            if not self.api_key:
                self.client = None
                print("⚠️ Azure OpenAI API key not configured")
            else:
                # Set up headers for Azure OpenAI API calls
                self.headers = {
                    "Content-Type": "application/json",
                    "api-key": self.api_key
                }
                self.client = True  # Flag to indicate it's configured
                print("✅ Azure OpenAI Vision API configured successfully!")
                print(f"✅ Using endpoint: {self.config['endpoint']}")
                print(f"✅ Using deployment: {self.config['deployment_name']}")
                
        except Exception as e:
            print(f"❌ Failed to initialize Azure OpenAI: {e}")
            self.client = None
            self.config = None
        
    def image_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 string
        
        Args:
            image: PIL Image object
            
        Returns:
            Base64 encoded image string
        """
        # Optimize image size for API
        max_size = (1024, 1024)
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Ensure RGB format
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=85, optimize=True)
        image_bytes = buffer.getvalue()
        
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def extract_document_data(self, image: Image.Image) -> Dict:
        """
        Extract structured data from any carbon footprint-related document using Azure OpenAI GPT-4 Vision
        
        Args:
            image: PIL Image of the document (receipt, bill, ticket, etc.)
            
        Returns:
            Dictionary with extracted document data
        """
        # Check if Azure OpenAI is available
        if not self.is_available():
            return {
                'success': False,
                'error': 'Azure OpenAI API not available',
                'text': 'OPENAI_ERROR: Azure OpenAI not configured properly',
                'category': 'others',
                'confidence': 0.0,
                'total_amount': 0.0,
                'amounts': [],
                'suggestions': ['Please check Azure OpenAI configuration']
            }
        
        try:
            # Convert image to base64
            base64_image = self.image_to_base64(image)
            
            # Use GPT-4 Vision for OCR and data extraction
            prompt = """
            You are an expert OCR system. Analyze this receipt/bill image and extract information for carbon footprint tracking.

            Extract the following:
            1. ALL visible text (complete OCR)
            2. Business/vendor name
            3. All item names and prices
            4. Total amount
            5. Date if visible

            Categorize as:
            - food: groceries, restaurants, food delivery
            - transport: gas, parking, taxi, transit, flights
            - appliances: utilities, electricity, gas bills
            - entertainment: movies, concerts, subscriptions
            - others: shopping, services, misc

            Return JSON format:
            {
                "success": true,
                "text": "complete extracted text",
                "category": "detected_category", 
                "confidence": 0.95,
                "total_amount": 25.50,
                "amounts": [{"amount": 15.99, "description": "item name", "quantity": 1}],
                "business_name": "Store Name",
                "suggestions": ["Carbon footprint suggestion"]
            }
            """
            
            # Prepare the payload for Azure OpenAI
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.1
            }
            
            # Make API call to Azure OpenAI
            url = f"{self.config['chat_endpoint']}?api-version={self.config['api_version']}"
            
            print(f"🔄 Making API call to Azure OpenAI...")
            print(f"📍 URL: {url}")
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"Azure OpenAI API error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'text': f'OPENAI_ERROR: {error_msg}',
                    'category': 'others',
                    'confidence': 0.0,
                    'total_amount': 0.0,
                    'amounts': [],
                    'suggestions': [f'Azure OpenAI API error: {response.status_code}']
                }
            
            # Parse the response
            response_data = response.json()
            content = response_data['choices'][0]['message']['content']
            print(f"✅ GPT-4 Vision Response: {content[:200]}...")  # Debug log
            
            # Extract JSON from response
            try:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    print(f"✅ Successfully parsed JSON response")
                else:
                    # Fallback if no JSON found
                    result = {
                        "success": True,
                        "text": content,
                        "category": "others",
                        "confidence": 0.5,
                        "total_amount": 0.0,
                        "amounts": [],
                        "suggestions": ["Manual review recommended - no structured data found"]
                    }
                    print("⚠️ No JSON found in response, using fallback")
            except json.JSONDecodeError as e:
                print(f"❌ JSON parsing failed: {e}")
                # Fallback for invalid JSON
                result = {
                    "success": True,
                    "text": content,
                    "category": "others", 
                    "confidence": 0.3,
                    "total_amount": 0.0,
                    "amounts": [],
                    "suggestions": ["JSON parsing failed, manual review needed"]
                }
            
            # Validate and enhance the result
            return self._validate_and_enhance_result(result)
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'text': f'OPENAI_ERROR: {error_msg}',
                'category': 'others',
                'confidence': 0.0,
                'total_amount': 0.0,
                'amounts': [],
                'suggestions': [f'Network error: {str(e)}']
            }
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Azure OpenAI Vision error: {error_msg}")
            
            return {
                'success': False,
                'error': f'Azure OpenAI Vision failed: {error_msg}',
                'text': f'OPENAI_ERROR: {error_msg}',
                'category': 'others',
                'confidence': 0.0,
                'total_amount': 0.0,
                'amounts': [],
                'suggestions': [f'Azure OpenAI Vision error: {error_msg}']
            }
    
    def _validate_and_enhance_result(self, result: Dict) -> Dict:
        """
        Validate and enhance the result from Azure OpenAI Vision
        """
        # Ensure required fields exist with defaults
        defaults = {
            'success': True,
            'text': "No text extracted",
            'category': 'others',
            'confidence': 0.5,
            'total_amount': 0.0,
            'amounts': [],
            'suggestions': []
        }
        
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value
        
        # Validate category
        valid_categories = ['food', 'transport', 'appliances', 'entertainment', 'others']
        if result['category'] not in valid_categories:
            result['category'] = 'others'
        
        # Validate confidence (0.0 to 1.0)
        try:
            confidence = float(result['confidence'])
            result['confidence'] = max(0.0, min(1.0, confidence))
        except:
            result['confidence'] = 0.5
        
        # Validate total_amount
        try:
            result['total_amount'] = float(result['total_amount'])
        except:
            result['total_amount'] = 0.0
        
        # Validate amounts array
        if not isinstance(result['amounts'], list):
            result['amounts'] = []
        
        # Add carbon footprint estimation based on category
        carbon_factors = {
            'food': 2.5,        # kg CO2 per dollar
            'transport': 0.5,   # kg CO2 per dollar  
            'appliances': 0.8,  # kg CO2 per dollar
            'entertainment': 0.3, # kg CO2 per dollar
            'others': 1.0       # kg CO2 per dollar
        }
        
        factor = carbon_factors.get(result['category'], 1.0)
        result['estimated_carbon_footprint'] = result['total_amount'] * factor
        
        print(f"✅ Validated result: {result['category']}, ${result['total_amount']}, {result['estimated_carbon_footprint']:.2f} kg CO2")
        
        return result
    
    def is_available(self) -> bool:
        """
        Check if Azure OpenAI OCR is available
        """
        return (AZURE_CONFIG_AVAILABLE and 
                self.config and 
                self.api_key and 
                self.client)
    
    def get_cost_estimate(self, image: Image.Image) -> float:
        """
        Estimate the cost of processing this image
        """
        # Azure OpenAI Vision pricing: ~$0.01-0.03 per image
        return 0.02
    
    def get_supported_document_types(self) -> List[str]:
        """
        Get list of supported document types
        """
        return [
            "Grocery receipts",
            "Restaurant bills", 
            "Gas station receipts",
            "Transit tickets",
            "Utility bills",
            "Shopping receipts"
        ]
    
    def get_supported_categories(self) -> List[str]:
        """
        Get list of supported categories
        """
        return ["food", "transport", "appliances", "entertainment", "others"] 