"""
Carbon Footprint Calculator Engine
Calculates CO2 emissions for different categories with emission factors
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple
import re

class CarbonCalculator:
    def __init__(self):
        # Emission factors (kg CO2 per unit)
        self.emission_factors = {
            'transport': {
                'car_petrol': 0.21,  # kg CO2 per km
                'car_diesel': 0.17,  # kg CO2 per km
                'car_hybrid': 0.12,  # kg CO2 per km
                'car_electric': 0.05, # kg CO2 per km
                'motorcycle': 0.103, # kg CO2 per km
                'scooter': 0.084,    # kg CO2 per km
                'bus': 0.089,        # kg CO2 per km
                'coach': 0.027,      # kg CO2 per km
                'train': 0.041,      # kg CO2 per km
                'tram': 0.029,       # kg CO2 per km
                'subway': 0.028,     # kg CO2 per km
                'metro': 0.028,      # kg CO2 per km
                'plane_domestic': 0.255,  # kg CO2 per km
                'plane_international': 0.150,  # kg CO2 per km
                'plane_short_haul': 0.274,    # kg CO2 per km
                'plane_long_haul': 0.195,     # kg CO2 per km
                'helicopter': 1.44,  # kg CO2 per km
                'taxi': 0.21,        # kg CO2 per km
                'uber': 0.21,        # kg CO2 per km
                'rideshare': 0.19,   # kg CO2 per km (shared)
                'ferry': 0.113,      # kg CO2 per km
                'cruise_ship': 0.285, # kg CO2 per km
                'bike': 0.0,         # kg CO2 per km
                'e_bike': 0.005,     # kg CO2 per km
                'walk': 0.0,         # kg CO2 per km
                'skateboard': 0.0,   # kg CO2 per km
                'scooter_kick': 0.0, # kg CO2 per km
            },
            'food': {
                'beef': 27.0,        # kg CO2 per kg
                'lamb': 24.5,        # kg CO2 per kg
                'pork': 12.1,        # kg CO2 per kg
                'chicken': 6.9,      # kg CO2 per kg
                'turkey': 5.8,       # kg CO2 per kg
                'fish': 4.0,         # kg CO2 per kg
                'salmon': 5.4,       # kg CO2 per kg
                'tuna': 4.9,         # kg CO2 per kg
                'shrimp': 11.8,      # kg CO2 per kg
                'vegetables': 2.0,   # kg CO2 per kg
                'fruits': 1.1,       # kg CO2 per kg
                'dairy': 3.2,        # kg CO2 per kg
                'milk': 1.9,         # kg CO2 per liter
                'cheese': 13.5,      # kg CO2 per kg
                'yogurt': 2.2,       # kg CO2 per kg
                'eggs': 4.2,         # kg CO2 per kg
                'rice': 2.7,         # kg CO2 per kg
                'pasta': 1.4,        # kg CO2 per kg
                'bread': 0.9,        # kg CO2 per kg
                'potatoes': 0.3,     # kg CO2 per kg
                'beans': 0.4,        # kg CO2 per kg
                'nuts': 0.3,         # kg CO2 per kg
                'pizza': 7.0,        # kg CO2 per pizza
                'burger': 12.0,      # kg CO2 per burger
                'sandwich': 2.5,     # kg CO2 per sandwich
                'salad': 1.5,        # kg CO2 per salad
                'soup': 1.8,         # kg CO2 per bowl
                'coffee': 0.02,      # kg CO2 per cup
                'tea': 0.006,        # kg CO2 per cup
                'soda': 0.5,         # kg CO2 per can
                'beer': 0.9,         # kg CO2 per bottle
                'wine': 1.3,         # kg CO2 per glass
                'ice_cream': 3.8,    # kg CO2 per serving
                'chocolate': 18.7,   # kg CO2 per kg
                'cake': 2.3,         # kg CO2 per slice
                'restaurant_meal': 8.0,  # kg CO2 per meal
                'fast_food': 5.0,    # kg CO2 per meal
                'takeout': 6.0,      # kg CO2 per meal
                'breakfast': 3.0,    # kg CO2 per meal
                'lunch': 4.0,        # kg CO2 per meal
                'dinner': 6.0,       # kg CO2 per meal
                'snack': 1.0,        # kg CO2 per snack
            },
            'appliances': {
                'electricity': 0.5,  # kg CO2 per kWh (average)
                'natural_gas': 2.0,  # kg CO2 per cubic meter
                'heating_oil': 2.5,  # kg CO2 per liter
                'coal': 2.4,         # kg CO2 per kg
                'wood': 0.0,         # kg CO2 per kg (renewable)
                'solar_panel': 0.0,  # kg CO2 per kWh
                'wind_energy': 0.0,  # kg CO2 per kWh
                'washing_machine': 0.6,  # kg CO2 per cycle
                'dryer': 2.3,        # kg CO2 per cycle
                'dishwasher': 0.8,   # kg CO2 per cycle
                'refrigerator': 1.2, # kg CO2 per day
                'freezer': 0.8,      # kg CO2 per day
                'microwave': 0.12,   # kg CO2 per use
                'oven': 1.4,         # kg CO2 per hour
                'stove': 0.9,        # kg CO2 per hour
                'air_conditioning': 2.5,  # kg CO2 per hour
                'heating': 1.8,      # kg CO2 per hour
                'fan': 0.05,         # kg CO2 per hour
                'space_heater': 1.5, # kg CO2 per hour
                'water_heater': 4.0, # kg CO2 per day
                'tv': 0.15,          # kg CO2 per hour
                'computer': 0.2,     # kg CO2 per hour
                'laptop': 0.05,      # kg CO2 per hour
                'phone_charging': 0.008, # kg CO2 per charge
                'vacuum': 0.4,       # kg CO2 per use
                'iron': 0.4,         # kg CO2 per use
                'hair_dryer': 0.3,   # kg CO2 per use
                'coffee_maker': 0.24, # kg CO2 per use
                'lights_led': 0.01,  # kg CO2 per hour
                'lights_incandescent': 0.04, # kg CO2 per hour
                'lights_fluorescent': 0.015, # kg CO2 per hour
            },
            'entertainment': {
                'streaming': 0.0036, # kg CO2 per hour
                'gaming': 0.12,      # kg CO2 per hour
                'gaming_console': 0.15, # kg CO2 per hour
                'mobile_gaming': 0.02,  # kg CO2 per hour
                'movie_theater': 1.5, # kg CO2 per ticket
                'concert': 3.0,      # kg CO2 per ticket
                'music_festival': 5.0, # kg CO2 per ticket
                'sports_event': 2.5, # kg CO2 per ticket
                'theater_play': 2.0, # kg CO2 per ticket
                'comedy_show': 1.8,  # kg CO2 per ticket
                'shopping': 5.0,     # kg CO2 per shopping trip
                'online_shopping': 2.0, # kg CO2 per order
                'gym': 1.2,          # kg CO2 per session
                'swimming_pool': 3.8, # kg CO2 per session
                'bowling': 4.0,      # kg CO2 per game
                'mini_golf': 1.0,    # kg CO2 per game
                'arcade': 2.0,       # kg CO2 per session
                'amusement_park': 15.0, # kg CO2 per visit
                'zoo': 8.0,          # kg CO2 per visit
                'museum': 3.0,       # kg CO2 per visit
                'art_gallery': 2.0,  # kg CO2 per visit
                'library': 0.5,      # kg CO2 per visit
                'book_reading': 0.0, # kg CO2 per hour
                'board_games': 0.0,  # kg CO2 per hour
                'video_call': 0.004, # kg CO2 per hour
                'social_media': 0.002, # kg CO2 per hour
                'podcast': 0.001,    # kg CO2 per hour
                'music_listening': 0.001, # kg CO2 per hour
            },
            'others': {
                'clothing': 10.0,    # kg CO2 per item
                'shoes': 8.0,        # kg CO2 per pair
                'jacket': 15.0,      # kg CO2 per item
                'jeans': 12.0,       # kg CO2 per pair
                't_shirt': 6.0,      # kg CO2 per item
                'dress': 18.0,       # kg CO2 per item
                'electronics': 300.0, # kg CO2 per device
                'smartphone': 70.0,  # kg CO2 per device
                'laptop': 400.0,     # kg CO2 per device
                'tablet': 130.0,     # kg CO2 per device
                'tv': 500.0,         # kg CO2 per device
                'camera': 150.0,     # kg CO2 per device
                'furniture': 50.0,   # kg CO2 per item
                'sofa': 90.0,        # kg CO2 per item
                'chair': 25.0,       # kg CO2 per item
                'table': 40.0,       # kg CO2 per item
                'bed': 60.0,         # kg CO2 per item
                'mattress': 35.0,    # kg CO2 per item
                'books': 1.0,        # kg CO2 per book
                'magazine': 0.3,     # kg CO2 per magazine
                'newspaper': 0.1,    # kg CO2 per paper
                'cosmetics': 3.0,    # kg CO2 per product
                'shampoo': 1.5,      # kg CO2 per bottle
                'soap': 0.8,         # kg CO2 per bar
                'toothpaste': 0.5,   # kg CO2 per tube
                'perfume': 4.0,      # kg CO2 per bottle
                'jewelry': 20.0,     # kg CO2 per item
                'watch': 15.0,       # kg CO2 per item
                'sunglasses': 8.0,   # kg CO2 per pair
                'bag': 12.0,         # kg CO2 per bag
                'backpack': 18.0,    # kg CO2 per backpack
                'luggage': 25.0,     # kg CO2 per suitcase
                'tools': 30.0,       # kg CO2 per tool
                'bicycle': 5.0,      # kg CO2 per bike
                'car_maintenance': 2.0, # kg CO2 per service
                'car_wash': 1.0,     # kg CO2 per wash
                'haircut': 2.0,      # kg CO2 per haircut
                'dental_visit': 3.0, # kg CO2 per visit
                'medical_checkup': 5.0, # kg CO2 per visit
            }
        }
    
    def calculate_carbon_footprint(self, category: str, item_type: str, 
                                 quantity: float, unit: str = None) -> float:
        """
        Calculate carbon footprint for a specific item
        
        Args:
            category: One of 'transport', 'food', 'appliances', 'entertainment', 'others'
            item_type: Specific item within the category
            quantity: Amount/quantity of the item
            unit: Unit of measurement (optional)
        
        Returns:
            Carbon footprint in kg CO2
        """
        if category not in self.emission_factors:
            return 0.0
        
        if item_type not in self.emission_factors[category]:
            # Use a default factor for unknown items
            default_factors = {
                'transport': 0.15,
                'food': 3.0,
                'appliances': 1.0,
                'entertainment': 2.0,
                'others': 5.0
            }
            emission_factor = default_factors.get(category, 1.0)
        else:
            emission_factor = self.emission_factors[category][item_type]
        
        return quantity * emission_factor
    
    def parse_text_entry(self, text: str) -> List[Dict]:
        """
        Parse natural language text to extract carbon footprint entries
        
        Args:
            text: Natural language description of activities
        
        Returns:
            List of parsed entries with category, item, quantity
        """
        entries = []
        text = text.lower().strip()
        
        # Transportation patterns (with specific distances)
        transport_patterns = [
            (r'drove (\d+(?:\.\d+)?)\s*(?:km|kilometers?|miles?)', 'car_petrol'),
            (r'(\d+(?:\.\d+)?)\s*(?:km|kilometers?|miles?) by car', 'car_petrol'),
            (r'took (?:a )?bus (\d+(?:\.\d+)?)\s*(?:km|kilometers?|miles?)', 'bus'),
            (r'(\d+(?:\.\d+)?)\s*(?:km|kilometers?|miles?) by bus', 'bus'),
            (r'train (\d+(?:\.\d+)?)\s*(?:km|kilometers?|miles?)', 'train'),
            (r'flew (\d+(?:\.\d+)?)\s*(?:km|kilometers?|miles?)', 'plane_domestic'),
            (r'flight (\d+(?:\.\d+)?)\s*(?:km|kilometers?|miles?)', 'plane_domestic'),
        ]
        
        # Transportation patterns (without specific distances - assume typical distances)
        transport_simple_patterns = [
            (r'walked (?:to )?(?:a |the )?(?:store|shop|market|mall)', ('walk', 1.0)),  # 1km to store
            (r'walked (?:to )?(?:work|office)', ('walk', 2.0)),  # 2km to work
            (r'walked home', ('walk', 2.0)),  # 2km home
            
            # Cycling/Biking patterns
            (r'(?:cycled|biked) (?:to )?(?:a |the )?(?:store|shop|market|mall)', ('bike', 3.0)),  # 3km to store
            (r'(?:cycled|biked) (?:to )?(?:work|office)', ('bike', 8.0)),  # 8km to work
            (r'(?:cycled|biked) (?:to )?(?:a |the )?(?:cinema|movie|theater)', ('bike', 5.0)),  # 5km to cinema
            (r'(?:cycled|biked) home', ('bike', 8.0)),  # 8km home
            (r'rode (?:a |my )?bike', ('bike', 5.0)),  # 5km general bike ride
            (r'went (?:by )?(?:bike|bicycle)', ('bike', 5.0)),  # 5km general bike ride
            (r'took (?:a |my )?bike', ('bike', 5.0)),  # 5km general bike ride
            
            # Car patterns
            (r'drove (?:to )?(?:a |the )?(?:store|shop|market|mall)', ('car_petrol', 3.0)),  # 3km to store
            (r'drove (?:to )?(?:work|office)', ('car_petrol', 15.0)),  # 15km to work
            (r'drove home', ('car_petrol', 15.0)),  # 15km home
            
            # Public transport patterns  
            (r'took (?:a |the )?bus (?:to )?(?:work|office)', ('bus', 12.0)),  # 12km to work
            (r'took (?:a |the )?bus (?:to )?(?:a |the )?(?:store|shop|mall)', ('bus', 5.0)),  # 5km to store
            (r'took (?:a |the )?train', ('train', 25.0)),  # 25km typical train ride
            
            # Air travel patterns
            (r'went (?:on a |on )?flight', ('plane_domestic', 500.0)),  # 500km typical domestic flight
            (r'flew somewhere', ('plane_domestic', 500.0)),  # 500km typical domestic flight
        ]
        
        # Food patterns (with specific quantities)
        food_patterns = [
            (r'ate (\d+(?:\.\d+)?)\s*(?:kg|kilograms?) of beef', 'beef'),
            (r'(\d+(?:\.\d+)?)\s*(?:kg|kilograms?) beef', 'beef'),
            (r'ate (\d+(?:\.\d+)?)\s*(?:kg|kilograms?) of chicken', 'chicken'),
            (r'(\d+(?:\.\d+)?)\s*restaurant meals?', 'restaurant_meal'),
            (r'(\d+(?:\.\d+)?)\s*meals? at restaurant', 'restaurant_meal'),
            (r'drank (\d+(?:\.\d+)?)\s*(?:cups? of )?coffee', 'coffee'),
            (r'had (\d+(?:\.\d+)?)\s*(?:cups? of )?coffee', 'coffee'),
            (r'ate (\d+(?:\.\d+)?)\s*(?:slices? of )?pizza', 'pizza'),
            (r'drank (\d+(?:\.\d+)?)\s*(?:bottles? of )?beer', 'beer'),
            (r'had (\d+(?:\.\d+)?)\s*(?:glasses? of )?wine', 'wine'),
        ]
        
        # Food patterns (without specific quantities - assume typical portions)
        food_simple_patterns = [
            # Restaurant/takeout patterns
            (r'ate (?:at )?(?:a |the )?restaurant', ('restaurant_meal', 1.0)),
            (r'had (?:a )?(?:restaurant )?meal', ('restaurant_meal', 1.0)),
            (r'went to (?:a |the )?restaurant', ('restaurant_meal', 1.0)),
            (r'ordered (?:some )?food', ('takeout', 1.0)),
            (r'got (?:some )?takeout', ('takeout', 1.0)),
            (r'ordered (?:a )?pizza', ('pizza', 1.0)),
            (r'ate (?:a )?pizza', ('pizza', 1.0)),
            (r'had (?:some )?fast food', ('fast_food', 1.0)),
            (r'went to (?:mcdonald|burger king|kfc|subway)', ('fast_food', 1.0)),
            
            # Meat patterns
            (r'ate (?:some )?beef', ('beef', 0.2)),
            (r'had (?:some )?beef', ('beef', 0.2)),
            (r'ate (?:a )?(?:beef )?burger', ('burger', 1.0)),
            (r'had (?:a )?(?:beef )?burger', ('burger', 1.0)),
            (r'ate (?:some )?steak', ('beef', 0.25)),
            (r'had (?:a )?steak', ('beef', 0.25)),
            
            # Chicken patterns  
            (r'ate (?:some )?chicken', ('chicken', 0.15)),
            (r'had (?:some )?chicken', ('chicken', 0.15)),
            (r'ate (?:.*)?chicken (?:rice|dish|meal)', ('chicken', 0.15)),
            (r'had (?:.*)?chicken (?:rice|dish|meal)', ('chicken', 0.15)),
            (r'ate (?:some )?(?:fried )?chicken', ('chicken', 0.15)),
            
            # Pork patterns
            (r'ate (?:some )?pork', ('pork', 0.15)),
            (r'had (?:some )?pork', ('pork', 0.15)),
            (r'ate (?:some )?bacon', ('pork', 0.05)),
            (r'had (?:some )?bacon', ('pork', 0.05)),
            (r'ate (?:some )?ham', ('pork', 0.1)),
            
            # Seafood patterns
            (r'ate (?:some )?fish', ('fish', 0.15)),
            (r'had (?:some )?fish', ('fish', 0.15)),
            (r'ate (?:some )?salmon', ('salmon', 0.15)),
            (r'had (?:some )?salmon', ('salmon', 0.15)),
            (r'ate (?:some )?tuna', ('tuna', 0.1)),
            (r'ate (?:some )?shrimp', ('shrimp', 0.1)),
            (r'had (?:some )?(?:sea)?food', ('fish', 0.15)),
            
            # Dairy patterns
            (r'drank (?:some )?milk', ('milk', 0.25)),
            (r'had (?:some )?milk', ('milk', 0.25)),
            (r'ate (?:some )?cheese', ('cheese', 0.05)),
            (r'had (?:some )?cheese', ('cheese', 0.05)),
            (r'ate (?:some )?yogurt', ('yogurt', 0.15)),
            (r'had (?:some )?yogurt', ('yogurt', 0.15)),
            (r'ate (?:some )?ice cream', ('ice_cream', 1.0)),
            (r'had (?:some )?ice cream', ('ice_cream', 1.0)),
            
            # Egg patterns
            (r'ate (?:some )?eggs?', ('eggs', 0.1)),
            (r'had (?:some )?eggs?', ('eggs', 0.1)),
            (r'ate (?:an? )?(?:scrambled |fried |boiled )?eggs?', ('eggs', 0.1)),
            
            # Vegetable patterns
            (r'ate (?:.*)?(?:vegetable|veggie)', ('vegetables', 0.3)),
            (r'had (?:.*)?(?:vegetable|veggie)', ('vegetables', 0.3)),
            (r'ate (?:.*)?(?:salad)', ('salad', 1.0)),
            (r'had (?:.*)?(?:salad)', ('salad', 1.0)),
            (r'ate (?:.*)?stir fry', ('vegetables', 0.3)),
            (r'had (?:.*)?stir fry', ('vegetables', 0.3)),
            (r'ate (?:some )?potatoes', ('potatoes', 0.2)),
            (r'had (?:some )?potatoes', ('potatoes', 0.2)),
            
            # Fruit patterns
            (r'ate (?:some )?(?:fruit|apple|banana|orange)', ('fruits', 0.2)),
            (r'had (?:some )?(?:fruit|apple|banana|orange)', ('fruits', 0.2)),
            
            # Grain patterns
            (r'ate (?:.*)?rice(?! and)', ('rice', 0.2)),
            (r'had (?:.*)?rice(?! and)', ('rice', 0.2)),
            (r'ate (?:some )?pasta', ('pasta', 0.15)),
            (r'had (?:some )?pasta', ('pasta', 0.15)),
            (r'ate (?:some )?bread', ('bread', 0.1)),
            (r'had (?:some )?bread', ('bread', 0.1)),
            (r'ate (?:a )?sandwich', ('sandwich', 1.0)),
            (r'had (?:a )?sandwich', ('sandwich', 1.0)),
            
            # Snack patterns
            (r'ate (?:some )?(?:nuts|almonds|peanuts)', ('nuts', 0.05)),
            (r'had (?:some )?(?:nuts|almonds|peanuts)', ('nuts', 0.05)),
            (r'ate (?:some )?chocolate', ('chocolate', 0.05)),
            (r'had (?:some )?chocolate', ('chocolate', 0.05)),
            (r'ate (?:a )?(?:snack)', ('snack', 1.0)),
            (r'had (?:a )?(?:snack)', ('snack', 1.0)),
            (r'ate (?:a )?(?:slice of )?cake', ('cake', 1.0)),
            (r'had (?:a )?(?:slice of )?cake', ('cake', 1.0)),
            
            # Beverage patterns
            (r'drank (?:a )?(?:cup of )?coffee', ('coffee', 1.0)),
            (r'had (?:a )?(?:cup of )?coffee', ('coffee', 1.0)),
            (r'drank (?:some )?tea', ('tea', 1.0)),
            (r'had (?:some )?tea', ('tea', 1.0)),
            (r'drank (?:a )?(?:can of )?soda', ('soda', 1.0)),
            (r'had (?:a )?(?:can of )?soda', ('soda', 1.0)),
            (r'drank (?:a )?(?:bottle of )?beer', ('beer', 1.0)),
            (r'had (?:a )?(?:bottle of )?beer', ('beer', 1.0)),
            (r'drank (?:a )?(?:glass of )?wine', ('wine', 1.0)),
            (r'had (?:a )?(?:glass of )?wine', ('wine', 1.0)),
            
            # Meal patterns
            (r'ate (?:my )?breakfast', ('breakfast', 1.0)),
            (r'had (?:my )?breakfast', ('breakfast', 1.0)),
            (r'ate (?:my )?lunch', ('lunch', 1.0)),
            (r'had (?:my )?lunch', ('lunch', 1.0)),
            (r'ate (?:my )?dinner', ('dinner', 1.0)),
            (r'had (?:my )?dinner', ('dinner', 1.0)),
            
            # General patterns
            (r'bought groceries', ('vegetables', 2.0)),
            (r'went grocery shopping', ('vegetables', 2.0)),
            (r'cooked (?:a )?meal', ('lunch', 1.0)),
            (r'made (?:some )?food', ('lunch', 1.0)),
        ]
        
        # Appliance patterns (with specific quantities)
        appliance_patterns = [
            (r'used (\d+(?:\.\d+)?)\s*kwh', 'electricity'),
            (r'(\d+(?:\.\d+)?)\s*kwh of electricity', 'electricity'),
            (r'(\d+(?:\.\d+)?)\s*hours? of air conditioning', 'air_conditioning'),
            (r'(\d+(?:\.\d+)?)\s*washing machine cycles?', 'washing_machine'),
            (r'watched tv for (\d+(?:\.\d+)?)\s*hours?', 'tv'),
            (r'used computer for (\d+(?:\.\d+)?)\s*hours?', 'computer'),
        ]
        
        # Appliance patterns (without specific quantities - assume typical usage)
        appliance_simple_patterns = [
            # Heating/Cooling
            (r'used (?:the )?air conditioning', ('air_conditioning', 2.0)),
            (r'turned on (?:the )?(?:ac|a/c)', ('air_conditioning', 2.0)),
            (r'used (?:the )?heating', ('heating', 3.0)),
            (r'turned on (?:the )?heating', ('heating', 3.0)),
            (r'used (?:a )?space heater', ('space_heater', 2.0)),
            (r'used (?:a )?fan', ('fan', 4.0)),
            
            # Kitchen appliances
            (r'used (?:the )?microwave', ('microwave', 1.0)),
            (r'microwaved (?:some )?food', ('microwave', 1.0)),
            (r'used (?:the )?oven', ('oven', 1.0)),
            (r'baked (?:something|food)', ('oven', 1.0)),
            (r'cooked on (?:the )?stove', ('stove', 0.5)),
            (r'used (?:the )?stove', ('stove', 0.5)),
            (r'made (?:some )?coffee', ('coffee_maker', 1.0)),
            (r'brewed (?:some )?coffee', ('coffee_maker', 1.0)),
            
            # Cleaning appliances
            (r'ran (?:the )?washing machine', ('washing_machine', 1.0)),
            (r'did (?:some )?laundry', ('washing_machine', 1.0)),
            (r'washed (?:my )?clothes', ('washing_machine', 1.0)),
            (r'used (?:the )?dryer', ('dryer', 1.0)),
            (r'dried (?:my )?clothes', ('dryer', 1.0)),
            (r'used (?:the )?dishwasher', ('dishwasher', 1.0)),
            (r'ran (?:the )?dishwasher', ('dishwasher', 1.0)),
            (r'vacuumed', ('vacuum', 1.0)),
            (r'used (?:the )?vacuum', ('vacuum', 1.0)),
            (r'ironed (?:my )?clothes', ('iron', 1.0)),
            (r'used (?:the )?iron', ('iron', 1.0)),
            
            # Electronics
            (r'watched (?:some )?tv', ('tv', 2.0)),
            (r'watched television', ('tv', 2.0)),
            (r'used (?:my )?computer', ('computer', 3.0)),
            (r'worked on (?:my )?computer', ('computer', 4.0)),
            (r'used (?:my )?laptop', ('laptop', 3.0)),
            (r'charged (?:my )?phone', ('phone_charging', 1.0)),
            (r'used (?:the )?hair dryer', ('hair_dryer', 1.0)),
            (r'dried (?:my )?hair', ('hair_dryer', 1.0)),
            
            # Lighting
            (r'turned on (?:the )?lights', ('lights_led', 4.0)),
            (r'had (?:the )?lights on', ('lights_led', 4.0)),
            (r'used (?:led )?lights', ('lights_led', 4.0)),
        ]
        
        # Entertainment patterns (with specific quantities)
        entertainment_patterns = [
            (r'(\d+(?:\.\d+)?)\s*hours? of streaming', 'streaming'),
            (r'(\d+(?:\.\d+)?)\s*hours? streaming', 'streaming'),
            (r'(\d+(?:\.\d+)?)\s*hours? gaming', 'gaming'),
            (r'(\d+(?:\.\d+)?)\s*movie tickets?', 'movie_theater'),
            (r'played games for (\d+(?:\.\d+)?)\s*hours?', 'gaming'),
            (r'watched netflix for (\d+(?:\.\d+)?)\s*hours?', 'streaming'),
        ]
        
        # Entertainment patterns (without specific quantities - assume typical usage)
        entertainment_simple_patterns = [
            # Movies & Shows
            (r'watched (?:a )?movie', ('movie_theater', 1.0)),
            (r'went to (?:the )?movies', ('movie_theater', 1.0)),
            (r'saw (?:a )?(?:film|movie)', ('movie_theater', 1.0)),
            (r'watched (?:some )?netflix', ('streaming', 1.5)),
            (r'watched (?:some )?youtube', ('streaming', 1.0)),
            (r'streamed (?:some )?(?:shows|videos)', ('streaming', 1.5)),
            (r'binged (?:a )?(?:show|series)', ('streaming', 4.0)),
            
            # Gaming
            (r'played (?:video )?games', ('gaming', 2.0)),
            (r'gamed', ('gaming', 2.0)),
            (r'played (?:on )?(?:console|pc|mobile)', ('gaming', 2.0)),
            (r'played (?:some )?mobile games', ('mobile_gaming', 1.0)),
            
            # Events & Activities
            (r'went to (?:a )?concert', ('concert', 1.0)),
            (r'attended (?:a )?concert', ('concert', 1.0)),
            (r'went to (?:a )?music festival', ('music_festival', 1.0)),
            (r'went to (?:a )?sports (?:game|event)', ('sports_event', 1.0)),
            (r'watched (?:a )?(?:game|match) live', ('sports_event', 1.0)),
            (r'went to (?:a )?(?:play|theater)', ('theater_play', 1.0)),
            (r'saw (?:a )?(?:play|show)', ('theater_play', 1.0)),
            (r'went to (?:a )?comedy show', ('comedy_show', 1.0)),
            
            # Physical Activities
            (r'went to (?:the )?gym', ('gym', 1.0)),
            (r'worked out', ('gym', 1.0)),
            (r'exercised', ('gym', 1.0)),
            (r'went swimming', ('swimming_pool', 1.0)),
            (r'swam', ('swimming_pool', 1.0)),
            (r'went bowling', ('bowling', 1.0)),
            (r'played (?:mini )?golf', ('mini_golf', 1.0)),
            (r'went to (?:an )?arcade', ('arcade', 1.0)),
            
            # Outings & Places
            (r'went to (?:an )?amusement park', ('amusement_park', 1.0)),
            (r'visited (?:a )?(?:theme park|amusement park)', ('amusement_park', 1.0)),
            (r'went to (?:the )?zoo', ('zoo', 1.0)),
            (r'visited (?:the )?zoo', ('zoo', 1.0)),
            (r'went to (?:a )?museum', ('museum', 1.0)),
            (r'visited (?:a )?museum', ('museum', 1.0)),
            (r'went to (?:an )?art gallery', ('art_gallery', 1.0)),
            (r'visited (?:an )?art gallery', ('art_gallery', 1.0)),
            (r'went to (?:the )?library', ('library', 1.0)),
            (r'visited (?:the )?library', ('library', 1.0)),
            
            # Shopping
            (r'went shopping', ('shopping', 1.0)),
            (r'went to (?:the )?(?:mall|store)', ('shopping', 1.0)),
            (r'bought (?:some )?clothes', ('shopping', 1.0)),
            (r'did (?:some )?shopping', ('shopping', 1.0)),
            (r'ordered (?:something )?online', ('online_shopping', 1.0)),
            (r'shopped online', ('online_shopping', 1.0)),
            
            # Social & Communication
            (r'had (?:a )?video call', ('video_call', 1.0)),
            (r'video called', ('video_call', 1.0)),
            (r'used (?:zoom|skype|teams)', ('video_call', 1.0)),
            (r'browsed (?:social )?media', ('social_media', 1.0)),
            (r'used (?:facebook|instagram|twitter)', ('social_media', 1.0)),
            (r'listened to (?:a )?podcast', ('podcast', 1.0)),
            (r'listened to (?:some )?music', ('music_listening', 2.0)),
            
            # Reading & Learning
            (r'read (?:a )?book', ('book_reading', 2.0)),
            (r'played (?:some )?board games', ('board_games', 2.0)),
            (r'did (?:a )?puzzle', ('board_games', 1.0)),
        ]
        
        # Others patterns (activities and purchases)
        others_simple_patterns = [
            # Clothing purchases
            (r'bought (?:a )?(?:t-?shirt|shirt)', ('t_shirt', 1.0)),
            (r'bought (?:some )?jeans', ('jeans', 1.0)),
            (r'bought (?:a )?(?:jacket|coat)', ('jacket', 1.0)),
            (r'bought (?:a )?dress', ('dress', 1.0)),
            (r'bought (?:some )?shoes', ('shoes', 1.0)),
            (r'bought (?:some )?(?:clothing|clothes)', ('clothing', 2.0)),
            
            # Electronics purchases
            (r'bought (?:a )?(?:new )?(?:smart)?phone', ('smartphone', 1.0)),
            (r'bought (?:a )?(?:new )?laptop', ('laptop', 1.0)),
            (r'bought (?:a )?(?:new )?tablet', ('tablet', 1.0)),
            (r'bought (?:a )?(?:new )?tv', ('tv', 1.0)),
            (r'bought (?:a )?(?:new )?camera', ('camera', 1.0)),
            (r'bought (?:some )?electronics', ('electronics', 1.0)),
            
            # Furniture purchases
            (r'bought (?:a )?(?:new )?sofa', ('sofa', 1.0)),
            (r'bought (?:a )?(?:new )?chair', ('chair', 1.0)),
            (r'bought (?:a )?(?:new )?table', ('table', 1.0)),
            (r'bought (?:a )?(?:new )?bed', ('bed', 1.0)),
            (r'bought (?:a )?(?:new )?mattress', ('mattress', 1.0)),
            (r'bought (?:some )?furniture', ('furniture', 1.0)),
            
            # Personal care & services
            (r'got (?:a )?haircut', ('haircut', 1.0)),
            (r'went to (?:the )?barber', ('haircut', 1.0)),
            (r'went to (?:the )?dentist', ('dental_visit', 1.0)),
            (r'had (?:a )?dental (?:appointment|checkup)', ('dental_visit', 1.0)),
            (r'went to (?:the )?doctor', ('medical_checkup', 1.0)),
            (r'had (?:a )?medical (?:appointment|checkup)', ('medical_checkup', 1.0)),
            (r'washed (?:my )?car', ('car_wash', 1.0)),
            (r'got (?:a )?car wash', ('car_wash', 1.0)),
            
            # Reading & media
            (r'bought (?:a )?book', ('books', 1.0)),
            (r'bought (?:a )?magazine', ('magazine', 1.0)),
            (r'bought (?:a )?newspaper', ('newspaper', 1.0)),
            
            # Cosmetics & accessories
            (r'bought (?:some )?(?:makeup|cosmetics)', ('cosmetics', 1.0)),
            (r'bought (?:some )?shampoo', ('shampoo', 1.0)),
            (r'bought (?:some )?soap', ('soap', 1.0)),
            (r'bought (?:some )?toothpaste', ('toothpaste', 1.0)),
            (r'bought (?:some )?perfume', ('perfume', 1.0)),
            (r'bought (?:some )?jewelry', ('jewelry', 1.0)),
            (r'bought (?:a )?watch', ('watch', 1.0)),
            (r'bought (?:some )?sunglasses', ('sunglasses', 1.0)),
            (r'bought (?:a )?(?:hand)?bag', ('bag', 1.0)),
            (r'bought (?:a )?backpack', ('backpack', 1.0)),
            (r'bought (?:some )?luggage', ('luggage', 1.0)),
        ]
        
        # Pattern groups with specific quantities
        pattern_groups = [
            ('transport', transport_patterns),
            ('food', food_patterns),
            ('appliances', appliance_patterns),
            ('entertainment', entertainment_patterns),
        ]
        
        # Pattern groups with assumed quantities
        simple_pattern_groups = [
            ('transport', transport_simple_patterns),
            ('food', food_simple_patterns),
            ('appliances', appliance_simple_patterns),
            ('entertainment', entertainment_simple_patterns),
            ('others', others_simple_patterns),
        ]
        
        # Process specific quantity patterns first
        for category, patterns in pattern_groups:
            for pattern, item_type in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    quantity = float(match) if isinstance(match, str) else float(match[0])
                    entries.append({
                        'category': category,
                        'item_type': item_type,
                        'quantity': quantity,
                        'carbon_footprint': self.calculate_carbon_footprint(category, item_type, quantity)
                    })
        
        # Also check simple patterns (regardless of whether specific patterns were found)
        matched_patterns = set()  # Track what we've already matched to avoid duplicates
        
        for category, patterns in simple_pattern_groups:
            for pattern, (item_type, quantity) in patterns:
                if re.search(pattern, text) and pattern not in matched_patterns:
                    # Check if we already have a specific pattern match for this category and item
                    existing_match = any(
                        entry['category'] == category and entry['item_type'] == item_type 
                        for entry in entries
                    )
                    if not existing_match:
                        entries.append({
                            'category': category,
                            'item_type': item_type,
                            'quantity': quantity,
                            'carbon_footprint': self.calculate_carbon_footprint(category, item_type, quantity)
                        })
                        matched_patterns.add(pattern)
        
        return entries
    
    def categorize_expense(self, description: str, amount: float = None) -> Dict:
        """
        Categorize an expense description into carbon footprint categories
        
        Args:
            description: Description of the expense
            amount: Amount spent (optional)
        
        Returns:
            Dictionary with category, estimated_quantity, and carbon_footprint
        """
        description = description.lower()
        
        # Transportation keywords
        transport_keywords = ['gas', 'fuel', 'petrol', 'diesel', 'uber', 'taxi', 'bus', 'train', 'flight', 'airline']
        food_keywords = ['restaurant', 'food', 'grocery', 'meal', 'cafe', 'coffee', 'pizza', 'burger']
        appliance_keywords = ['electricity', 'electric', 'gas bill', 'utility', 'heating', 'cooling']
        entertainment_keywords = ['movie', 'cinema', 'concert', 'game', 'netflix', 'spotify', 'entertainment']
        
        # Simple keyword-based categorization
        if any(keyword in description for keyword in transport_keywords):
            category = 'transport'
            # Estimate based on amount (rough calculation)
            if amount:
                estimated_km = amount / 1.5  # Assume $1.5 per km
                carbon_footprint = self.calculate_carbon_footprint('transport', 'car_petrol', estimated_km)
            else:
                carbon_footprint = 10.0  # Default estimate
            return {
                'category': category,
                'item_type': 'car_petrol',
                'estimated_quantity': estimated_km if amount else 10,
                'carbon_footprint': carbon_footprint
            }
        
        elif any(keyword in description for keyword in food_keywords):
            category = 'food'
            if amount:
                estimated_meals = amount / 15  # Assume $15 per restaurant meal
                carbon_footprint = self.calculate_carbon_footprint('food', 'restaurant_meal', estimated_meals)
            else:
                carbon_footprint = 8.0
            return {
                'category': category,
                'item_type': 'restaurant_meal',
                'estimated_quantity': estimated_meals if amount else 1,
                'carbon_footprint': carbon_footprint
            }
        
        elif any(keyword in description for keyword in appliance_keywords):
            category = 'appliances'
            if amount:
                estimated_kwh = amount / 0.12  # Assume $0.12 per kWh
                carbon_footprint = self.calculate_carbon_footprint('appliances', 'electricity', estimated_kwh)
            else:
                carbon_footprint = 50.0
            return {
                'category': category,
                'item_type': 'electricity',
                'estimated_quantity': estimated_kwh if amount else 100,
                'carbon_footprint': carbon_footprint
            }
        
        elif any(keyword in description for keyword in entertainment_keywords):
            category = 'entertainment'
            if amount:
                estimated_tickets = amount / 12  # Assume $12 per movie ticket
                carbon_footprint = self.calculate_carbon_footprint('entertainment', 'movie_theater', estimated_tickets)
            else:
                carbon_footprint = 1.5
            return {
                'category': category,
                'item_type': 'movie_theater',
                'estimated_quantity': estimated_tickets if amount else 1,
                'carbon_footprint': carbon_footprint
            }
        
        else:
            # Default to 'others' category
            return {
                'category': 'others',
                'item_type': 'general',
                'estimated_quantity': 1,
                'carbon_footprint': 5.0  # Default estimate
            }

    def get_category_breakdown(self, entries: List[Dict]) -> Dict[str, float]:
        """
        Get carbon footprint breakdown by category
        
        Args:
            entries: List of carbon footprint entries
        
        Returns:
            Dictionary with category totals
        """
        breakdown = {
            'transport': 0.0,
            'food': 0.0,
            'appliances': 0.0,
            'entertainment': 0.0,
            'others': 0.0
        }
        
        for entry in entries:
            category = entry.get('category', 'others')
            carbon_footprint = entry.get('carbon_footprint', 0.0)
            breakdown[category] += carbon_footprint
        
        return breakdown
    
    def get_recommendations(self, breakdown: Dict[str, float]) -> List[str]:
        """
        Get personalized recommendations based on carbon footprint breakdown
        
        Args:
            breakdown: Category breakdown of carbon footprint
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        total = sum(breakdown.values())
        
        if total == 0:
            return ["Start tracking your activities to get personalized recommendations!"]
        
        # Transportation recommendations
        transport_percentage = (breakdown['transport'] / total) * 100
        if transport_percentage > 40:
            recommendations.append("🚗 Transportation is your largest emission source. Consider using public transport, carpooling, or cycling more often.")
        elif transport_percentage > 25:
            recommendations.append("🚌 Try combining trips or using public transportation to reduce your transport emissions.")
        
        # Food recommendations
        food_percentage = (breakdown['food'] / total) * 100
        if food_percentage > 30:
            recommendations.append("🥗 Consider reducing meat consumption and eating more plant-based meals to lower your food-related emissions.")
        elif food_percentage > 20:
            recommendations.append("🌱 Try having one meat-free day per week to reduce your food carbon footprint.")
        
        # Appliance recommendations
        appliance_percentage = (breakdown['appliances'] / total) * 100
        if appliance_percentage > 35:
            recommendations.append("⚡ Your home energy use is high. Consider using energy-efficient appliances and LED lighting.")
        elif appliance_percentage > 20:
            recommendations.append("🏠 Turn off appliances when not in use and consider adjusting your thermostat by 1-2 degrees.")
        
        # Entertainment recommendations
        entertainment_percentage = (breakdown['entertainment'] / total) * 100
        if entertainment_percentage > 20:
            recommendations.append("🎬 Consider more low-carbon entertainment options like reading, hiking, or local activities.")
        
        if not recommendations:
            recommendations.append("🎉 Great job! Your carbon footprint is well-balanced. Keep up the good work!")
        
        return recommendations 