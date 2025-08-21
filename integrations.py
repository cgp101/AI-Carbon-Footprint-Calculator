"""
External Integrations Module
Connects with fitness apps, banking APIs, smart home devices, and other data sources
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
from abc import ABC, abstractmethod

class BaseIntegration(ABC):
    """Base class for all external integrations"""
    
    def __init__(self, api_key: str = None, config: Dict = None):
        self.api_key = api_key
        self.config = config or {}
        self.last_sync = None
        
    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the external service"""
        pass
    
    @abstractmethod
    def fetch_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch data from the external service"""
        pass
    
    @abstractmethod
    def convert_to_emissions(self, raw_data: Dict) -> List[Dict]:
        """Convert raw data to carbon emission entries"""
        pass

class FitnessIntegration(BaseIntegration):
    """Integration with fitness apps (Strava, Google Fit, Apple Health)"""
    
    def __init__(self, provider: str, api_key: str = None, config: Dict = None):
        super().__init__(api_key, config)
        self.provider = provider.lower()
        self.base_urls = {
            'strava': 'https://www.strava.com/api/v3',
            'google_fit': 'https://www.googleapis.com/fitness/v1',
            'apple_health': 'https://developer.apple.com/healthkit'  # Note: Requires iOS app
        }
        
    def authenticate(self) -> bool:
        """Authenticate with fitness service"""
        try:
            if self.provider == 'strava':
                return self._authenticate_strava()
            elif self.provider == 'google_fit':
                return self._authenticate_google_fit()
            else:
                return False
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _authenticate_strava(self) -> bool:
        """Authenticate with Strava API"""
        if not self.api_key:
            return False
        
        headers = {'Authorization': f'Bearer {self.api_key}'}
        response = requests.get(f"{self.base_urls['strava']}/athlete", headers=headers)
        return response.status_code == 200
    
    def _authenticate_google_fit(self) -> bool:
        """Authenticate with Google Fit API"""
        # Google Fit requires OAuth2 - simplified mock implementation
        return bool(self.api_key)
    
    def fetch_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch fitness/transport data"""
        try:
            if self.provider == 'strava':
                return self._fetch_strava_activities(start_date, end_date)
            elif self.provider == 'google_fit':
                return self._fetch_google_fit_data(start_date, end_date)
            else:
                return {}
        except Exception as e:
            return {"error": f"Failed to fetch data: {e}"}
    
    def _fetch_strava_activities(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch activities from Strava"""
        headers = {'Authorization': f'Bearer {self.api_key}'}
        params = {
            'after': int(start_date.timestamp()),
            'before': int(end_date.timestamp()),
            'per_page': 100
        }
        
        response = requests.get(
            f"{self.base_urls['strava']}/athlete/activities",
            headers=headers,
            params=params
        )
        
        if response.status_code == 200:
            return {"activities": response.json()}
        else:
            return {"error": f"Strava API error: {response.status_code}"}
    
    def _fetch_google_fit_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch data from Google Fit (mock implementation)"""
        # Mock data for demonstration
        return {
            "activities": [
                {
                    "type": "cycling",
                    "distance": 15.2,
                    "duration": 3600,
                    "date": start_date.isoformat()
                },
                {
                    "type": "walking",
                    "distance": 5.8,
                    "duration": 2400,
                    "date": (start_date + timedelta(days=1)).isoformat()
                }
            ]
        }
    
    def convert_to_emissions(self, raw_data: Dict) -> List[Dict]:
        """Convert fitness data to carbon emissions"""
        emissions = []
        
        if "error" in raw_data:
            return emissions
        
        activities = raw_data.get("activities", [])
        
        # Transport mode mappings and emission factors
        transport_mappings = {
            'cycling': {'mode': 'bike', 'factor': 0.0},
            'running': {'mode': 'walk', 'factor': 0.0},
            'walking': {'mode': 'walk', 'factor': 0.0},
            'ride': {'mode': 'car_petrol', 'factor': 0.21},  # Strava "Ride" could be cycling or motorcycle
            'car': {'mode': 'car_petrol', 'factor': 0.21},
            'ebike': {'mode': 'e_bike', 'factor': 0.005}
        }
        
        for activity in activities:
            activity_type = activity.get('type', '').lower()
            distance = activity.get('distance', 0) / 1000  # Convert meters to km
            
            if activity_type in transport_mappings:
                transport_info = transport_mappings[activity_type]
                carbon_footprint = distance * transport_info['factor']
                
                emissions.append({
                    'date': activity.get('start_date', activity.get('date', datetime.now().isoformat())),
                    'category': 'transport',
                    'subcategory': transport_info['mode'],
                    'quantity': distance,
                    'unit': 'km',
                    'carbon_footprint': carbon_footprint,
                    'source': f'{self.provider}_integration',
                    'description': f"{activity_type.title()} - {distance:.1f} km",
                    'raw_data': activity
                })
        
        return emissions

class SmartHomeIntegration(BaseIntegration):
    """Integration with smart home devices and energy monitoring"""
    
    def __init__(self, provider: str, api_key: str = None, config: Dict = None):
        super().__init__(api_key, config)
        self.provider = provider.lower()
        self.base_urls = {
            'tesla': 'https://owner-api.teslamotors.com',
            'nest': 'https://developer-api.nest.com',
            'smartthings': 'https://api.smartthings.com/v1',
            'sense': 'https://api.sense.com/apiservice/api/v1'
        }
    
    def authenticate(self) -> bool:
        """Authenticate with smart home service"""
        try:
            if self.provider == 'tesla':
                return self._authenticate_tesla()
            elif self.provider == 'sense':
                return self._authenticate_sense()
            else:
                return bool(self.api_key)
        except Exception as e:
            print(f"Smart home authentication failed: {e}")
            return False
    
    def _authenticate_tesla(self) -> bool:
        """Authenticate with Tesla API"""
        # Tesla OAuth implementation would go here
        return bool(self.api_key)
    
    def _authenticate_sense(self) -> bool:
        """Authenticate with Sense energy monitor"""
        # Sense authentication implementation
        return bool(self.api_key)
    
    def fetch_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch smart home energy data"""
        try:
            if self.provider == 'tesla':
                return self._fetch_tesla_data(start_date, end_date)
            elif self.provider == 'sense':
                return self._fetch_sense_data(start_date, end_date)
            else:
                return self._fetch_generic_energy_data(start_date, end_date)
        except Exception as e:
            return {"error": f"Failed to fetch smart home data: {e}"}
    
    def _fetch_tesla_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch Tesla vehicle and energy data"""
        # Mock Tesla data
        return {
            "energy_usage": [
                {
                    "date": start_date.isoformat(),
                    "home_energy": 45.2,
                    "solar_production": 38.7,
                    "vehicle_charging": 15.8,
                    "net_usage": 22.3
                }
            ],
            "vehicle_data": [
                {
                    "date": start_date.isoformat(),
                    "miles_driven": 45.2,
                    "energy_used": 15.8,
                    "efficiency": 0.35
                }
            ]
        }
    
    def _fetch_sense_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch Sense energy monitoring data"""
        # Mock Sense data
        return {
            "energy_usage": [
                {
                    "date": start_date.isoformat(),
                    "total_usage": 28.4,
                    "solar_production": 12.1,
                    "device_breakdown": {
                        "hvac": 12.5,
                        "water_heater": 4.2,
                        "refrigerator": 2.1,
                        "lighting": 1.8,
                        "other": 7.8
                    }
                }
            ]
        }
    
    def _fetch_generic_energy_data(self, start_date: datetime, end_date: datetime) -> Dict:
        """Fetch generic smart home energy data"""
        return {
            "energy_usage": [
                {
                    "date": start_date.isoformat(),
                    "electricity_kwh": 25.0,
                    "gas_usage": 15.0,
                    "water_usage": 150.0
                }
            ]
        }
    
    def convert_to_emissions(self, raw_data: Dict) -> List[Dict]:
        """Convert smart home data to carbon emissions"""
        emissions = []
        
        if "error" in raw_data:
            return emissions
        
        energy_data = raw_data.get("energy_usage", [])
        vehicle_data = raw_data.get("vehicle_data", [])
        
        # Convert energy usage
        for entry in energy_data:
            date = entry.get("date", datetime.now().isoformat())
            
            # Electricity emissions
            if "total_usage" in entry:
                electricity_kwh = entry["total_usage"]
                solar_production = entry.get("solar_production", 0)
                net_electricity = max(0, electricity_kwh - solar_production)
                
                emissions.append({
                    'date': date,
                    'category': 'appliances',
                    'subcategory': 'electricity',
                    'quantity': net_electricity,
                    'unit': 'kWh',
                    'carbon_footprint': net_electricity * 0.5,  # 0.5 kg CO2 per kWh
                    'source': f'{self.provider}_integration',
                    'description': f"Home electricity usage - {net_electricity:.1f} kWh (net of solar)",
                    'raw_data': entry
                })
            
            # Gas usage
            if "gas_usage" in entry:
                gas_usage = entry["gas_usage"]
                emissions.append({
                    'date': date,
                    'category': 'appliances',
                    'subcategory': 'natural_gas',
                    'quantity': gas_usage,
                    'unit': 'cubic meters',
                    'carbon_footprint': gas_usage * 2.0,  # 2.0 kg CO2 per cubic meter
                    'source': f'{self.provider}_integration',
                    'description': f"Natural gas usage - {gas_usage:.1f} cubic meters",
                    'raw_data': entry
                })
        
        # Convert vehicle data
        for entry in vehicle_data:
            date = entry.get("date", datetime.now().isoformat())
            miles_driven = entry.get("miles_driven", 0)
            km_driven = miles_driven * 1.60934  # Convert miles to km
            
            emissions.append({
                'date': date,
                'category': 'transport',
                'subcategory': 'car_electric',
                'quantity': km_driven,
                'unit': 'km',
                'carbon_footprint': km_driven * 0.05,  # 0.05 kg CO2 per km for electric
                'source': f'{self.provider}_integration',
                'description': f"Electric vehicle - {km_driven:.1f} km",
                'raw_data': entry
            })
        
        return emissions

class WeatherIntegration(BaseIntegration):
    """Integration with weather services for climate impact analysis"""
    
    def __init__(self, api_key: str = None, config: Dict = None):
        super().__init__(api_key, config)
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def authenticate(self) -> bool:
        """Authenticate with weather service"""
        if not self.api_key:
            return False
        
        # Test API key with a simple call
        test_url = f"{self.base_url}/weather?q=London&appid={self.api_key}"
        try:
            response = requests.get(test_url)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, start_date: datetime, end_date: datetime, location: str = "auto") -> Dict:
        """Fetch weather data for carbon footprint analysis"""
        try:
            # For historical weather, you'd typically use a different endpoint
            # This is a simplified implementation
            params = {
                'q': location if location != "auto" else "New York",
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(f"{self.base_url}/weather", params=params)
            
            if response.status_code == 200:
                return {"weather_data": response.json()}
            else:
                return {"error": f"Weather API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Failed to fetch weather data: {e}"}
    
    def convert_to_emissions(self, raw_data: Dict) -> List[Dict]:
        """Convert weather data to emission factors (for heating/cooling analysis)"""
        emissions = []
        
        if "error" in raw_data:
            return emissions
        
        weather = raw_data.get("weather_data", {})
        main = weather.get("main", {})
        
        # Calculate heating/cooling degree days
        temp = main.get("temp", 20)  # Current temperature
        base_temp = 18  # Base temperature for heating/cooling
        
        if temp < base_temp:
            # Heating needed
            heating_degree_days = base_temp - temp
            estimated_heating_kwh = heating_degree_days * 5  # Rough estimate
            
            emissions.append({
                'date': datetime.now().isoformat(),
                'category': 'appliances',
                'subcategory': 'heating',
                'quantity': estimated_heating_kwh,
                'unit': 'kWh',
                'carbon_footprint': estimated_heating_kwh * 0.5,
                'source': 'weather_integration',
                'description': f"Estimated heating due to {temp:.1f}°C temperature",
                'confidence': 'estimated',
                'raw_data': weather
            })
        elif temp > 25:
            # Cooling needed
            cooling_degree_days = temp - 25
            estimated_cooling_kwh = cooling_degree_days * 3  # Rough estimate
            
            emissions.append({
                'date': datetime.now().isoformat(),
                'category': 'appliances',
                'subcategory': 'air_conditioning',
                'quantity': estimated_cooling_kwh,
                'unit': 'kWh',
                'carbon_footprint': estimated_cooling_kwh * 0.5,
                'source': 'weather_integration',
                'description': f"Estimated cooling due to {temp:.1f}°C temperature",
                'confidence': 'estimated',
                'raw_data': weather
            })
        
        return emissions

class IntegrationManager:
    """Manages all external integrations"""
    
    def __init__(self):
        self.integrations = {}
        self.sync_history = {}
    
    def add_integration(self, name: str, integration: BaseIntegration) -> bool:
        """Add a new integration"""
        if integration.authenticate():
            self.integrations[name] = integration
            return True
        return False
    
    def sync_all_integrations(self, start_date: datetime, end_date: datetime) -> Dict:
        """Sync data from all active integrations"""
        all_emissions = []
        sync_results = {}
        
        for name, integration in self.integrations.items():
            try:
                raw_data = integration.fetch_data(start_date, end_date)
                emissions = integration.convert_to_emissions(raw_data)
                
                all_emissions.extend(emissions)
                sync_results[name] = {
                    'success': True,
                    'entries_count': len(emissions),
                    'last_sync': datetime.now().isoformat()
                }
                
            except Exception as e:
                sync_results[name] = {
                    'success': False,
                    'error': str(e),
                    'last_sync': datetime.now().isoformat()
                }
        
        return {
            'emissions': all_emissions,
            'sync_results': sync_results,
            'total_entries': len(all_emissions)
        }
    
    def get_available_integrations(self) -> List[Dict]:
        """Get list of available integrations and their status"""
        return [
            {
                'name': name,
                'type': type(integration).__name__,
                'authenticated': integration.authenticate(),
                'last_sync': self.sync_history.get(name, {}).get('last_sync'),
                'provider': getattr(integration, 'provider', 'unknown')
            }
            for name, integration in self.integrations.items()
        ] 