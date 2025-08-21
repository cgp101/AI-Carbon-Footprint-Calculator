"""
Image Processing Module for OCR
Processes uploaded bills and transit tickets to extract carbon footprint related information
"""

import cv2
import numpy as np
from PIL import Image
import re
from typing import List, Dict, Tuple
import os

# Import OpenAI OCR module
try:
    from openai_ocr import OpenAIOCR
    OPENAI_AVAILABLE = True
    print("OpenAI Vision OCR available")
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI not available. Photo upload feature will be disabled.")

class ImageProcessor:
    """
    Image processor using OpenAI GPT-4 Vision for superior receipt OCR
    """
    
    def __init__(self):
        """Initialize the image processor with OpenAI OCR"""
        self.openai_ocr = None
        
        # Initialize OpenAI OCR
        if OPENAI_AVAILABLE:
            try:
                # Try to get API key from config
                try:
                    from config import get_openai_key
                    api_key = get_openai_key()
                    if api_key and api_key != "your-openai-api-key-here":
                        self.openai_ocr = OpenAIOCR(api_key=api_key)
                        print("OpenAI Vision OCR initialized successfully with config key!")
                    else:
                        print("OpenAI API key not configured in config.py")
                        self.openai_ocr = None
                except ImportError:
                    # Fallback to environment variable
                    self.openai_ocr = OpenAIOCR()
                    if self.openai_ocr.is_available():
                        print("OpenAI Vision OCR initialized successfully with env key!")
                    else:
                        print("OpenAI API key not found in environment")
                        self.openai_ocr = None
            except Exception as e:
                print(f"Failed to initialize OpenAI OCR: {e}")
                self.openai_ocr = None
        
        if not self.openai_ocr:
            print("OpenAI OCR not available. Photo upload will use mock data.")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Basic image preprocessing for better OCR results
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to OpenCV format
        img_array = np.array(image)
        
        # Ensure minimum size for better OCR
        height, width = img_array.shape[:2]
        if height < 600:
            scale_factor = 600 / height
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img_array = cv2.resize(img_array, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Convert to grayscale for processing
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Convert back to PIL Image
        return Image.fromarray(enhanced).convert('RGB')
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from image using OpenAI GPT-4 Vision
        
        Args:
            image: PIL Image object
            
        Returns:
            Extracted text as string
        """
        if not self.openai_ocr:
            print("OpenAI OCR not available. Using mock OCR for testing...")
            mock_text = self.mock_ocr_for_testing(image)
            return f"MOCK_OCR: {mock_text}"
        
        try:
            print("Using OpenAI GPT-4 Vision for receipt analysis...")
            
            # Get cost estimate
            estimated_cost = self.openai_ocr.get_cost_estimate(image)
            print(f"Estimated cost: ${estimated_cost:.4f}")
            
            # Extract structured data using OpenAI Vision
            result = self.openai_ocr.extract_document_data(image)
            
            if result['success']:
                data = result['data']
                
                # Convert structured data back to text format for compatibility
                lines = []
                
                # Add document header
                doc_type = data.get('document_type', 'other').replace('_', ' ').title()
                business_name = data.get('business_name', 'Unknown Business')
                if business_name != 'Unknown Business':
                    lines.append(f"{business_name} - {doc_type}")
                else:
                    lines.append(doc_type)
                
                # Add date if available
                if data.get('date'):
                    lines.append(f"Date: {data['date']}")
                
                # Add transport details if available
                transport = data.get('transport_details', {})
                if transport.get('mode'):
                    transport_line = f"Transport: {transport['mode']}"
                    if transport.get('distance', 0) > 0:
                        unit = transport.get('distance_unit', 'miles')
                        transport_line += f" - {transport['distance']} {unit}"
                    if transport.get('origin') and transport.get('destination'):
                        transport_line += f" from {transport['origin']} to {transport['destination']}"
                    lines.append(transport_line)
                
                # Add utility details if available
                utility = data.get('utility_details', {})
                if utility.get('service_type'):
                    utility_line = f"Utility: {utility['service_type']}"
                    if utility.get('usage_amount', 0) > 0:
                        unit = utility.get('usage_unit', 'units')
                        utility_line += f" - {utility['usage_amount']} {unit}"
                    if utility.get('billing_period'):
                        utility_line += f" ({utility['billing_period']})"
                    lines.append(utility_line)
                
                # Add items/services
                for item in data.get('items', []):
                    price = item.get('price', 0.0)
                    name = item.get('name', 'Unknown Item')
                    quantity = item.get('quantity', 1)
                    category = item.get('category', 'other')
                    unit = item.get('unit', 'each')
                    
                    if quantity > 1 and unit != 'each':
                        line = f"{name} ({quantity} {unit}) [${price:.2f}] - {category}"
                    elif quantity > 1:
                        line = f"{name} ({quantity}x) [${price:.2f}] - {category}"
                    else:
                        line = f"{name} [${price:.2f}] - {category}"
                    lines.append(line)
                
                # Add totals
                totals = data.get('totals', {})
                if totals.get('subtotal', 0) > 0:
                    lines.append(f"SUBTOTAL ${totals['subtotal']:.2f}")
                if totals.get('tax', 0) > 0:
                    lines.append(f"TAX ${totals['tax']:.2f}")
                if totals.get('fees', 0) > 0:
                    lines.append(f"FEES ${totals['fees']:.2f}")
                if totals.get('total', 0) > 0:
                    lines.append(f"TOTAL ${totals['total']:.2f}")
                
                # Add carbon footprint info
                carbon_data = data.get('carbon_relevant_data', {})
                if carbon_data.get('primary_category'):
                    lines.append(f"Category: {carbon_data['primary_category']}")
                
                # Include raw text if available
                if data.get('raw_text'):
                    lines.append(f"\n--- Raw OCR Text ---\n{data['raw_text']}")
                
                # Add processing notes
                if data.get('processing_notes'):
                    lines.append(f"\n--- Notes ---\n{data['processing_notes']}")
                
                extracted_text = '\n'.join(lines)
                
                # Store the structured data for later use
                self._last_structured_data = data
                self._last_usage = result.get('usage', {})
                
                confidence = carbon_data.get('confidence_level', 0.5)
                item_count = len(data.get('items', []))
                
                print(f"OpenAI Vision processed {doc_type}: {item_count} items with confidence {confidence:.2f}")
                print(f"Document category: {carbon_data.get('primary_category', 'unknown')}")
                print(f"API Usage - Tokens: {result.get('usage', {}).get('total_tokens', 0)}")
                
                return extracted_text
                
            else:
                print(f"OpenAI Vision failed: {result.get('error', 'Unknown error')}")
                return f"OPENAI_ERROR: {result.get('error', 'Unknown error')}"
        
        except Exception as e:
            print(f"Error during OpenAI Vision processing: {e}")
            return f"OCR_ERROR: {str(e)}"
    
    def extract_amounts_and_descriptions(self, text: str) -> List[Dict]:
        """
        Extract amounts and descriptions from text or use structured data if available
        
        Args:
            text: OCR extracted text
            
        Returns:
            List of dictionaries with amount and description
        """
        # If we have structured data from OpenAI, use that instead
        if hasattr(self, '_last_structured_data') and self._last_structured_data:
            data = self._last_structured_data
            results = []
            
            for item in data.get('items', []):
                results.append({
                    'amount': float(item.get('price', 0.0)),
                    'description': item.get('name', 'Unknown Item'),
                    'context': f"{item.get('name', 'Unknown Item')} ${item.get('price', 0.0):.2f}",
                    'quantity': item.get('quantity', 1)
                })
            
            # Sort by amount (highest first)
            results.sort(key=lambda x: x['amount'], reverse=True)
            
            print(f"Using structured data: {len(results)} items extracted")
            return results
        
        # Fallback to text parsing (in case structured data is not available)
        return self._parse_text_amounts(text)
    
    def _parse_text_amounts(self, text: str) -> List[Dict]:
        """
        Fallback text parsing for amounts and descriptions
        
        Args:
            text: OCR text
            
        Returns:
            List of dictionaries with amount and description
        """
        results = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if len(line) < 3:
                continue
                
            # Look for price patterns
            price_patterns = [
                r'\$(\d+\.\d{2})',  # $13.90
                r'(\d+\.\d{2})',    # 13.90
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, line)
                for match in matches:
                    try:
                        price = float(match)
                        if 0.01 <= price <= 1000.00:
                            # Extract description (everything before the price)
                            desc_part = re.sub(r'\$?\d+\.\d{2}.*', '', line).strip()
                            if not desc_part:
                                desc_part = "Unknown Item"
                            
                            results.append({
                                'amount': price,
                                'description': desc_part,
                                'context': line,
                                'quantity': 1
                            })
                            break
                    except ValueError:
                        continue
        
        # Remove duplicates and sort
        unique_results = []
        seen_amounts = set()
        
        for result in results:
            if result['amount'] not in seen_amounts:
                seen_amounts.add(result['amount'])
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: x['amount'], reverse=True)
        return unique_results
    
    def categorize_from_text(self, text: str) -> Tuple[str, float, str]:
        """
        Categorize the expense from text with enhanced OpenAI context
        
        Args:
            text: OCR extracted text
            
        Returns:
            Tuple of (category, confidence, subtype)
        """
        # If we have structured data from OpenAI, use that
        if hasattr(self, '_last_structured_data') and self._last_structured_data:
            data = self._last_structured_data
            carbon_data = data.get('carbon_relevant_data', {})
            
            # Use the AI-determined category and confidence
            primary_category = carbon_data.get('primary_category', 'others')
            confidence = carbon_data.get('confidence_level', 0.5)
            
            # Determine subtype based on document and business type
            doc_type = data.get('document_type', 'other')
            business_type = data.get('business_type', 'other')
            
            # Map to our category system with subtypes
            if primary_category == 'food':
                if doc_type in ['grocery_receipt'] or business_type in ['grocery', 'supermarket']:
                    return 'food', confidence, 'grocery'
                elif doc_type in ['restaurant_bill'] or business_type in ['restaurant']:
                    return 'food', confidence, 'restaurant'
                else:
                    return 'food', confidence, 'food'
            
            elif primary_category == 'transport':
                if doc_type in ['gas_receipt', 'fuel_receipt'] or business_type in ['gas_station']:
                    return 'transport', confidence, 'fuel'
                elif doc_type in ['transit_ticket', 'airline_ticket']:
                    return 'transport', confidence, 'transit'
                else:
                    return 'transport', confidence, 'transport'
            
            elif primary_category == 'appliances':
                if business_type in ['electronics', 'retail']:
                    return 'appliances', confidence, 'electronics'
                else:
                    return 'appliances', confidence, 'appliances'
            
            elif primary_category == 'entertainment':
                return 'entertainment', confidence, 'entertainment'
            
            else:  # others or unknown
                if doc_type == 'utility_bill':
                    utility_type = data.get('utility_details', {}).get('service_type', 'utility')
                    return 'others', confidence, utility_type
                else:
                    return 'others', confidence, 'general'
        
        # Fallback to text-based categorization
        return self._categorize_from_text_fallback(text)
    
    def _categorize_from_items(self, items: List[Dict], base_confidence: float) -> Tuple[str, float, str]:
        """
        Categorize based on item analysis
        
        Args:
            items: List of items with names and prices
            base_confidence: Base confidence from OpenAI
            
        Returns:
            Tuple of (category, confidence, subtype)
        """
        if not items:
            return 'others', 0.3, 'unknown'
        
        # Analyze item names
        food_keywords = ['bread', 'milk', 'chicken', 'beef', 'fruit', 'vegetable', 'rice', 'pasta', 'cheese']
        restaurant_keywords = ['meal', 'combo', 'burger', 'pizza', 'drink', 'beverage', 'entree']
        transport_keywords = ['gas', 'fuel', 'diesel', 'petrol']
        appliance_keywords = ['tv', 'phone', 'computer', 'electronics', 'appliance']
        
        category_scores = {
            'food_grocery': 0,
            'food_restaurant': 0,
            'transport': 0,
            'appliances': 0,
            'others': 0
        }
        
        for item in items:
            name = item.get('name', '').lower()
            
            for keyword in food_keywords:
                if keyword in name:
                    category_scores['food_grocery'] += 1
            
            for keyword in restaurant_keywords:
                if keyword in name:
                    category_scores['food_restaurant'] += 1
            
            for keyword in transport_keywords:
                if keyword in name:
                    category_scores['transport'] += 1
            
            for keyword in appliance_keywords:
                if keyword in name:
                    category_scores['appliances'] += 1
        
        # Determine category
        max_score = max(category_scores.values())
        if max_score == 0:
            return 'others', base_confidence * 0.5, 'unknown'
        
        best_category = max(category_scores, key=category_scores.get)
        
        if best_category == 'food_grocery':
            return 'food', base_confidence, 'grocery'
        elif best_category == 'food_restaurant':
            return 'food', base_confidence, 'restaurant'
        elif best_category == 'transport':
            return 'transport', base_confidence, 'fuel'
        elif best_category == 'appliances':
            return 'appliances', base_confidence, 'electronics'
        else:
            return 'others', base_confidence, 'unknown'
    
    def _categorize_from_text_fallback(self, text: str) -> Tuple[str, float, str]:
        """
        Fallback text-based categorization
        
        Args:
            text: OCR text
            
        Returns:
            Tuple of (category, confidence, subtype)
        """
        text_lower = text.lower()
        
        # Simple keyword matching
        if any(word in text_lower for word in ['grocery', 'supermarket', 'market']):
            return 'food', 0.8, 'grocery'
        elif any(word in text_lower for word in ['restaurant', 'cafe', 'dining']):
            return 'food', 0.8, 'restaurant'
        elif any(word in text_lower for word in ['gas', 'fuel', 'petrol']):
            return 'transport', 0.8, 'fuel'
        else:
            return 'others', 0.3, 'unknown'
    
    def _generate_suggestions(self, category: str, total_amount: float, item_count: int, subtype: str = None) -> List[str]:
        """
        Generate AI suggestions based on the analysis
        
        Args:
            category: Detected category
            total_amount: Total amount spent
            item_count: Number of items
            subtype: Category subtype
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        if category == 'food':
            if subtype == 'grocery':
                avg_per_item = total_amount / max(item_count, 1)
                suggestions.append(f"Grocery shopping: {item_count} items, ${avg_per_item:.2f} average per item")
                suggestions.append(f"Total grocery spend: ${total_amount:.2f}")
                
                if total_amount > 100:
                    suggestions.append("💡 Consider buying in bulk for better unit prices")
                if item_count > 20:
                    suggestions.append("📝 Large shopping trip - good for meal planning")
            
            elif subtype == 'restaurant':
                suggestions.append(f"Restaurant meal: ${total_amount:.2f}")
                if total_amount > 50:
                    suggestions.append("🍽️ Fine dining or group meal")
                else:
                    suggestions.append("🍔 Casual dining or fast food")
        
        elif category == 'transport':
            suggestions.append(f"Fuel purchase: ${total_amount:.2f}")
            if total_amount > 50:
                suggestions.append("⛽ Full tank or large vehicle")
        
        elif category == 'appliances':
            suggestions.append(f"Electronics/Appliances: ${total_amount:.2f}")
            if total_amount > 500:
                suggestions.append("📱 Major electronics purchase")
        
        else:
            suggestions.append(f"General purchase: ${total_amount:.2f}")
        
        # Add environmental tip
        if hasattr(self, '_last_structured_data'):
            data = self._last_structured_data
            confidence = data.get('confidence', 0.5)
            suggestions.append(f"🎯 Analysis confidence: {confidence:.1%}")
        
        return suggestions
    
    def mock_ocr_for_testing(self, image: Image.Image) -> str:
        """
        Generate mock OCR text for testing when OpenAI is not available
        
        Args:
            image: PIL Image object
            
        Returns:
            Mock OCR text string
        """
        width, height = image.size
        
        # Generate different mock documents based on image characteristics
        if width > height:  # Landscape - could be utility bill or airline ticket
            if width / height > 1.5:  # Very wide - likely airline ticket
                return """SKYLINE AIRLINES - Airline Ticket
Date: 2024-01-15
Flight: SL1234 from NYC to LAX
Distance: 2,445 miles
Passenger: John Doe
Base Fare [$299.00] - transport
Taxes [$45.50] - transport
TOTAL $344.50
Category: transport"""
            else:  # Wide - likely utility bill
                return """CITY POWER COMPANY - Utility Bill
Date: 2024-01-15
Service Period: Dec 2023
Electricity Usage: 850 kWh
Rate: $0.12/kWh
Energy Charge [$102.00] - electricity
Service Fee [$25.00] - electricity
TOTAL $127.00
Category: others"""
        
        else:  # Portrait - typical receipt
            aspect_ratio = height / width
            if aspect_ratio > 1.8:  # Very tall - likely gas station receipt
                return """QUICK FUEL STATION - Gas Receipt
Date: 2024-01-15
Pump #3
Regular Unleaded: 12.5 gallons
Price per gallon: $3.45
Fuel [$43.13] - fuel
TOTAL $43.13
Category: transport"""
            else:  # Normal - grocery receipt
                return """FRESH MARKET GROCERY - Grocery Receipt
Date: 2024-01-15
Organic Bananas [$3.49] - food
Whole Wheat Bread [$4.99] - food
Chicken Breast [$12.99] - food
Milk 2% Gallon [$3.79] - food
Spinach Organic [$5.99] - food
SUBTOTAL $31.25
TAX $2.50
TOTAL $33.75
Category: food""" 

    def process_receipt_image(self, image: Image.Image) -> Dict:
        """
        Main method to process receipt images using OpenAI or fallback
        
        Args:
            image: PIL Image object of the receipt
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Try OpenAI Vision first if available
            if self.openai_ocr and self.openai_ocr.is_available():
                result = self.openai_ocr.extract_document_data(image)
                return result
            else:
                # Fallback to basic OCR processing
                return self._process_with_basic_ocr(image)
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to process image: {str(e)}",
                'text': '',
                'category': 'others',
                'confidence': 0.0,
                'total_amount': 0.0,
                'amounts': [],
                'suggestions': [f"Error occurred: {str(e)}"]
            }
    
    def _process_with_basic_ocr(self, image: Image.Image) -> Dict:
        """
        Fallback processing using basic OCR methods
        
        Args:
            image: PIL Image object
            
        Returns:
            Dictionary with processing results
        """
        try:
            # Extract text using basic OCR
            text = self.extract_text_from_image(image)
            
            if not text:
                # Use mock data for testing
                text = self.mock_ocr_for_testing(image)
            
            # Extract amounts and categorize
            amounts = self.extract_amounts_and_descriptions(text)
            category, confidence, subtype = self.categorize_from_text(text)
            
            total_amount = sum(item['amount'] for item in amounts) if amounts else 0.0
            item_count = len(amounts)
            
            suggestions = self._generate_suggestions(category, total_amount, item_count, subtype)
            
            return {
                'success': True,
                'text': text,
                'category': category,
                'confidence': confidence,
                'total_amount': total_amount,
                'amounts': amounts,
                'suggestions': suggestions,
                'subtype': subtype
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Basic OCR failed: {str(e)}",
                'text': '',
                'category': 'others',
                'confidence': 0.0,
                'total_amount': 0.0,
                'amounts': [],
                'suggestions': [f"Basic OCR error: {str(e)}"]
            }

