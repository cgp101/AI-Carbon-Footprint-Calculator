"""
Location-based Carbon Tracking
Automatically detects transport modes and calculates emissions based on location data
"""

import json
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import requests
from geopy.distance import geodesic
import numpy as np

class LocationTracker:
    def __init__(self, google_maps_api_key: str = None):
        self.google_maps_api_key = google_maps_api_key
        self.location_history = []
        self.transport_thresholds = {
            'walking': {'min_speed': 0, 'max_speed': 8},      # km/h
            'cycling': {'min_speed': 8, 'max_speed': 35},     # km/h
            'driving': {'min_speed': 20, 'max_speed': 150},   # km/h
            'public_transport': {'min_speed': 15, 'max_speed': 80},  # km/h
            'flight': {'min_speed': 300, 'max_speed': 1000}   # km/h
        }
        
        # Emission factors for different transport modes (kg CO2 per km)
        self.emission_factors = {
            'walking': 0.0,
            'cycling': 0.0,
            'e_bike': 0.005,
            'car_petrol': 0.21,
            'car_diesel': 0.17,
            'car_hybrid': 0.12,
            'car_electric': 0.05,
            'bus': 0.089,
            'train': 0.041,
            'subway': 0.028,
            'tram': 0.029,
            'flight_domestic': 0.255,
            'flight_international': 0.150,
            'taxi': 0.21,
            'rideshare': 0.19
        }
    
    def geocode_location(self, location_name: str) -> Optional[Tuple[float, float]]:
        """Convert location name to coordinates using geocoding"""
        # Try multiple geocoding methods in order of preference
        
        # Method 1: Try geopy Nominatim with SSL fix
        coords = self._try_geopy_nominatim(location_name)
        if coords:
            return coords
        
        # Method 2: Try direct HTTP request to Nominatim (bypasses SSL issues)
        coords = self._try_direct_nominatim(location_name)
        if coords:
            return coords
        
        # Method 3: Try alternative geocoding service (LocationIQ/OpenCage style)
        coords = self._try_alternative_geocoding(location_name)
        if coords:
            return coords
        
        # Method 4: Try Google Maps if API key is available
        if self.google_maps_api_key:
            coords = self._try_google_maps(location_name)
            if coords:
                return coords
        
        # Method 5: Fallback to common locations
        return self._fallback_geocoding(location_name)
    
    def _try_geopy_nominatim(self, location_name: str) -> Optional[Tuple[float, float]]:
        """Try geocoding with geopy Nominatim"""
        try:
            from geopy.geocoders import Nominatim
            import ssl
            
            # Create SSL context that handles certificate verification
            try:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            except:
                ssl_context = None
            
            # Initialize geocoder with SSL context
            geolocator = Nominatim(
                user_agent="carbon_footprint_tracker",
                ssl_context=ssl_context
            )
            
            # Geocode the location
            location = geolocator.geocode(location_name, timeout=10)
            
            if location:
                return (location.latitude, location.longitude)
                
        except Exception as e:
            print(f"Geopy Nominatim error: {e}")
        
        return None
    
    def _try_direct_nominatim(self, location_name: str) -> Optional[Tuple[float, float]]:
        """Try direct HTTP request to Nominatim (bypasses SSL issues)"""
        try:
            import urllib.parse
            import urllib.request
            import json
            import ssl
            
            # Create SSL context that doesn't verify certificates
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Encode the location name for URL
            encoded_location = urllib.parse.quote(location_name)
            
            # Nominatim API URL
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1"
            
            # Create request with custom headers
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'carbon_footprint_tracker/1.0')
            
            # Make the request with SSL context
            with urllib.request.urlopen(request, context=ssl_context, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if data and len(data) > 0:
                    result = data[0]
                    lat = float(result['lat'])
                    lon = float(result['lon'])
                    return (lat, lon)
                    
        except Exception as e:
            print(f"Direct Nominatim error: {e}")
        
        return None
    
    def _try_alternative_geocoding(self, location_name: str) -> Optional[Tuple[float, float]]:
        """Try alternative geocoding using a different approach"""
        try:
            import urllib.parse
            import urllib.request
            import json
            
            # Use a simpler HTTP-based approach that doesn't rely on SSL
            # This uses OpenStreetMap's Nominatim but with insecure HTTP
            encoded_location = urllib.parse.quote(location_name)
            
            # Try HTTP version (less secure but works around SSL issues)
            url = f"http://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1"
            
            # Create request with custom headers
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'carbon_footprint_tracker/1.0')
            
            # Make the request
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if data and len(data) > 0:
                    result = data[0]
                    lat = float(result['lat'])
                    lon = float(result['lon'])
                    print(f"Alternative geocoding success: {location_name} -> ({lat}, {lon})")
                    return (lat, lon)
                    
        except Exception as e:
            print(f"Alternative geocoding error: {e}")
        
        return None
    
    def _try_google_maps(self, location_name: str) -> Optional[Tuple[float, float]]:
        """Try Google Maps Geocoding API if key is available"""
        try:
            import urllib.parse
            import urllib.request
            import json
            
            if not self.google_maps_api_key:
                return None
            
            # Encode the location name for URL
            encoded_location = urllib.parse.quote(location_name)
            
            # Google Maps Geocoding API URL
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_location}&key={self.google_maps_api_key}"
            
            # Make the request
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                if data['status'] == 'OK' and data['results']:
                    result = data['results'][0]
                    location = result['geometry']['location']
                    return (location['lat'], location['lng'])
                    
        except Exception as e:
            print(f"Google Maps error: {e}")
        
        return None
    
    def _fallback_geocoding(self, location_name: str) -> Optional[Tuple[float, float]]:
        """Fallback geocoding for common locations when main service fails"""
        # Common locations database (latitude, longitude)
        common_locations = {
            # Vancouver locations
            'robson street, vancouver': (49.2827, -123.1207),
            'robson square, vancouver': (49.2827, -123.1207),
            'rogers arena, vancouver': (49.2778, -123.1089),
            'roger arena, vancouver': (49.2778, -123.1089),  # Common misspelling
            'stanley park, vancouver': (49.3017, -123.1408),
            'granville island, vancouver': (49.2717, -123.1351),
            'granville street, vancouver': (49.2827, -123.1207),
            'vancouver international airport': (49.1939, -123.1844),
            'yvr': (49.1939, -123.1844),
            'downtown vancouver': (49.2827, -123.1207),
            'gastown, vancouver': (49.2839, -123.1094),
            'chinatown, vancouver': (49.2792, -123.1013),
            'yaletown, vancouver': (49.2745, -123.1214),
            'kitsilano, vancouver': (49.2659, -123.1556),
            'ubc, vancouver': (49.2606, -123.2460),
            'burnaby': (49.2488, -122.9805),
            'richmond, bc': (49.1666, -123.1336),
            'surrey, bc': (49.1913, -122.8490),
            
            # International locations
            'central park, new york': (40.7829, -73.9654),
            'central park, nyc': (40.7829, -73.9654),
            'times square, new york': (40.7580, -73.9855),
            'times square, nyc': (40.7580, -73.9855),
            'eiffel tower, paris': (48.8584, 2.2945),
            'london bridge, london': (51.5081, -0.0759),
            'sydney opera house, sydney': (-33.8568, 151.2153),
            'statue of liberty, new york': (40.6892, -74.0445),
            'golden gate bridge, san francisco': (37.8199, -122.4783),
            'tokyo tower, tokyo': (35.6586, 139.7454),
            
            # Major cities
            'vancouver': (49.2827, -123.1207),
            'vancouver, bc': (49.2827, -123.1207),
            'new york': (40.7128, -74.0060),
            'paris': (48.8566, 2.3522),
            'london': (51.5074, -0.1278),
            'tokyo': (35.6762, 139.6503),
            'sydney': (-33.8688, 151.2093),
            'san francisco': (37.7749, -122.4194),
            'toronto': (43.6532, -79.3832),
            'montreal': (45.5017, -73.5673),
            'calgary': (51.0447, -114.0719),
            'edmonton': (53.5461, -113.4938),
            
            # Generic locations
            'home': (49.2827, -123.1207),  # Default to Vancouver
            'office': (49.2827, -123.1207),  # Default to Vancouver
            'work': (49.2827, -123.1207),
            'airport': (49.1939, -123.1844),  # Default to YVR
            'downtown': (49.2827, -123.1207),
            'mall': (49.2827, -123.1207),
            'shopping center': (49.2827, -123.1207)
        }
        
        # Normalize the location name for lookup
        location_key = location_name.lower().strip()
        
        # Direct match
        if location_key in common_locations:
            print(f"Fallback geocoding success (direct): {location_name} -> {common_locations[location_key]}")
            return common_locations[location_key]
        
        # Try partial matching for city names and landmarks
        for key, coords in common_locations.items():
            # Check if any word from the location matches
            location_words = location_key.split()
            key_words = key.split(',')[0].split()  # Take the first part before comma
            
            # If any significant word matches (length > 3 to avoid short words)
            for loc_word in location_words:
                for key_word in key_words:
                    if len(loc_word) > 3 and len(key_word) > 3 and loc_word in key_word:
                        print(f"Fallback geocoding success (partial): {location_name} -> {coords}")
                        return coords
        
        print(f"Fallback geocoding failed: No match found for '{location_name}'")
        return None
    
    def add_location_point(self, latitude: float, longitude: float, timestamp: datetime = None, accuracy: float = None) -> Dict:
        """Add a location point to the tracking history"""
        if timestamp is None:
            timestamp = datetime.now()
        
        location_point = {
            'latitude': latitude,
            'longitude': longitude,
            'timestamp': timestamp,
            'accuracy': accuracy or 10.0  # meters
        }
        
        self.location_history.append(location_point)
        
        # Keep only last 1000 points to manage memory
        if len(self.location_history) > 1000:
            self.location_history = self.location_history[-1000:]
        
        return location_point
    
    def detect_trips(self, time_threshold_minutes: int = 5, distance_threshold_meters: int = 100) -> List[Dict]:
        """Detect trips from location history"""
        if len(self.location_history) < 2:
            return []
        
        trips = []
        current_trip = None
        stationary_start = None
        
        sorted_history = sorted(self.location_history, key=lambda x: x['timestamp'])
        
        for i in range(1, len(sorted_history)):
            prev_point = sorted_history[i-1]
            curr_point = sorted_history[i]
            
            # Calculate distance and time between points
            distance = self._calculate_distance(
                prev_point['latitude'], prev_point['longitude'],
                curr_point['latitude'], curr_point['longitude']
            )
            
            time_diff = (curr_point['timestamp'] - prev_point['timestamp']).total_seconds() / 60  # minutes
            
            if distance > distance_threshold_meters:
                # Movement detected
                if current_trip is None:
                    # Start new trip
                    current_trip = {
                        'start_point': prev_point,
                        'end_point': curr_point,
                        'points': [prev_point, curr_point],
                        'total_distance': distance,
                        'start_time': prev_point['timestamp'],
                        'end_time': curr_point['timestamp']
                    }
                else:
                    # Continue current trip
                    current_trip['end_point'] = curr_point
                    current_trip['points'].append(curr_point)
                    current_trip['total_distance'] += distance
                    current_trip['end_time'] = curr_point['timestamp']
                
                stationary_start = None
            else:
                # Stationary or slow movement
                if stationary_start is None:
                    stationary_start = curr_point['timestamp']
                
                # Check if we've been stationary long enough to end the trip
                if current_trip and stationary_start:
                    stationary_duration = (curr_point['timestamp'] - stationary_start).total_seconds() / 60
                    
                    if stationary_duration >= time_threshold_minutes:
                        # End current trip
                        trips.append(self._finalize_trip(current_trip))
                        current_trip = None
                        stationary_start = None
        
        # Add final trip if still ongoing
        if current_trip:
            trips.append(self._finalize_trip(current_trip))
        
        return trips
    
    def _finalize_trip(self, trip: Dict) -> Dict:
        """Finalize trip with calculated metrics and transport mode detection"""
        # Calculate total duration
        total_duration = (trip['end_time'] - trip['start_time']).total_seconds() / 3600  # hours
        
        # Calculate average speed
        distance_km = trip['total_distance'] / 1000  # Convert to km
        avg_speed = distance_km / total_duration if total_duration > 0 else 0
        
        # Detect transport mode
        transport_mode = self._detect_transport_mode(avg_speed, distance_km, trip['points'])
        
        # Calculate emissions
        emission_factor = self.emission_factors.get(transport_mode, 0.21)  # Default to petrol car
        carbon_footprint = distance_km * emission_factor
        
        # Add location context
        start_location = self._get_location_context(trip['start_point'])
        end_location = self._get_location_context(trip['end_point'])
        
        finalized_trip = {
            **trip,
            'distance_km': distance_km,
            'duration_hours': total_duration,
            'avg_speed_kmh': avg_speed,
            'detected_transport_mode': transport_mode,
            'emission_factor': emission_factor,
            'carbon_footprint': carbon_footprint,
            'start_location': start_location,
            'end_location': end_location,
            'trip_id': f"trip_{trip['start_time'].strftime('%Y%m%d_%H%M%S')}"
        }
        
        return finalized_trip
    
    def _detect_transport_mode(self, avg_speed: float, distance_km: float, points: List[Dict]) -> str:
        """Detect the most likely transport mode based on speed and patterns"""
        
        # Rule-based detection with speed thresholds
        if avg_speed <= self.transport_thresholds['walking']['max_speed']:
            if distance_km < 0.5:
                return 'walking'
            else:
                # Could be cycling for longer distances at walking speeds
                return 'cycling'
        
        elif avg_speed <= self.transport_thresholds['cycling']['max_speed']:
            return 'cycling'
        
        elif avg_speed >= self.transport_thresholds['flight']['min_speed']:
            return 'flight_domestic' if distance_km < 1000 else 'flight_international'
        
        else:
            # In driving range - need to determine car vs public transport
            # Analyze movement patterns
            if self._is_public_transport_pattern(points, avg_speed):
                if avg_speed < 25:
                    return 'bus'
                elif avg_speed < 60:
                    return 'train'
                else:
                    return 'train'  # High-speed rail
            else:
                # Assume private vehicle
                return 'car_petrol'  # Default assumption
    
    def _is_public_transport_pattern(self, points: List[Dict], avg_speed: float) -> bool:
        """Analyze if movement pattern suggests public transport"""
        if len(points) < 3:
            return False
        
        # Public transport typically has:
        # 1. Regular stops
        # 2. Consistent routes
        # 3. Specific speed patterns
        
        stops_detected = 0
        speed_variations = []
        
        for i in range(2, len(points)):
            prev_point = points[i-2]
            curr_point = points[i-1]
            next_point = points[i]
            
            # Calculate local speed
            dist1 = self._calculate_distance(
                prev_point['latitude'], prev_point['longitude'],
                curr_point['latitude'], curr_point['longitude']
            )
            time1 = (curr_point['timestamp'] - prev_point['timestamp']).total_seconds() / 3600
            speed1 = (dist1 / 1000) / time1 if time1 > 0 else 0
            
            dist2 = self._calculate_distance(
                curr_point['latitude'], curr_point['longitude'],
                next_point['latitude'], next_point['longitude']
            )
            time2 = (next_point['timestamp'] - curr_point['timestamp']).total_seconds() / 3600
            speed2 = (dist2 / 1000) / time2 if time2 > 0 else 0
            
            # Detect stops (significant speed reduction)
            if speed1 > 10 and speed2 < 5:
                stops_detected += 1
            
            speed_variations.append(abs(speed1 - speed2))
        
        # Heuristics for public transport
        avg_speed_variation = np.mean(speed_variations) if speed_variations else 0
        stop_frequency = stops_detected / len(points) if len(points) > 0 else 0
        
        # Public transport tends to have more stops and speed variations
        return stop_frequency > 0.1 or avg_speed_variation > 15
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters"""
        try:
            return geodesic((lat1, lon1), (lat2, lon2)).meters
        except:
            # Fallback to haversine formula
            return self._haversine_distance(lat1, lon1, lat2, lon2)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance using haversine formula (fallback)"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _get_location_context(self, point: Dict) -> Dict:
        """Get location context using reverse geocoding"""
        if not self.google_maps_api_key:
            return {
                'address': 'Unknown location',
                'type': 'unknown',
                'coordinates': f"{point['latitude']:.6f}, {point['longitude']:.6f}"
            }
        
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                'latlng': f"{point['latitude']},{point['longitude']}",
                'key': self.google_maps_api_key
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if data['results']:
                    result = data['results'][0]
                    address = result.get('formatted_address', 'Unknown')
                    
                    # Determine location type
                    location_type = 'unknown'
                    for component in result.get('address_components', []):
                        types = component.get('types', [])
                        if 'transit_station' in types:
                            location_type = 'transit_station'
                            break
                        elif 'airport' in types:
                            location_type = 'airport'
                            break
                        elif 'establishment' in types:
                            location_type = 'establishment'
                        elif 'route' in types:
                            location_type = 'road'
                    
                    return {
                        'address': address,
                        'type': location_type,
                        'coordinates': f"{point['latitude']:.6f}, {point['longitude']:.6f}",
                        'place_id': result.get('place_id')
                    }
            
            return {
                'address': 'Geocoding failed',
                'type': 'unknown',
                'coordinates': f"{point['latitude']:.6f}, {point['longitude']:.6f}"
            }
            
        except Exception as e:
            return {
                'address': f'Error: {str(e)}',
                'type': 'unknown',
                'coordinates': f"{point['latitude']:.6f}, {point['longitude']:.6f}"
            }
    
    def get_daily_summary(self, date: datetime = None) -> Dict:
        """Get daily transport summary for a specific date"""
        if date is None:
            date = datetime.now().date()
        
        # Filter trips for the specified date
        trips = self.detect_trips()
        daily_trips = [trip for trip in trips if trip['start_time'].date() == date]
        
        if not daily_trips:
            return {
                'date': date.isoformat(),
                'total_trips': 0,
                'total_distance_km': 0,
                'total_emissions_kg': 0,
                'transport_modes': {},
                'trips': []
            }
        
        # Calculate summary statistics
        total_distance = sum(trip['distance_km'] for trip in daily_trips)
        total_emissions = sum(trip['carbon_footprint'] for trip in daily_trips)
        
        # Group by transport mode
        transport_modes = {}
        for trip in daily_trips:
            mode = trip['detected_transport_mode']
            if mode not in transport_modes:
                transport_modes[mode] = {
                    'trip_count': 0,
                    'total_distance_km': 0,
                    'total_emissions_kg': 0
                }
            
            transport_modes[mode]['trip_count'] += 1
            transport_modes[mode]['total_distance_km'] += trip['distance_km']
            transport_modes[mode]['total_emissions_kg'] += trip['carbon_footprint']
        
        return {
            'date': date.isoformat(),
            'total_trips': len(daily_trips),
            'total_distance_km': round(total_distance, 2),
            'total_emissions_kg': round(total_emissions, 2),
            'transport_modes': transport_modes,
            'trips': daily_trips
        }
    
    def convert_trips_to_emission_entries(self, trips: List[Dict]) -> List[Dict]:
        """Convert detected trips to standardized emission entries"""
        entries = []
        
        for trip in trips:
            entry = {
                'date': trip['start_time'].isoformat(),
                'category': 'transport',
                'subcategory': trip['detected_transport_mode'],
                'quantity': trip['distance_km'],
                'unit': 'km',
                'carbon_footprint': trip['carbon_footprint'],
                'source': 'location_tracking',
                'description': f"{trip['detected_transport_mode'].title()} trip from {trip['start_location']['address']} to {trip['end_location']['address']}",
                'confidence': 'auto_detected',
                'metadata': {
                    'trip_id': trip['trip_id'],
                    'duration_hours': trip['duration_hours'],
                    'avg_speed_kmh': trip['avg_speed_kmh'],
                    'start_location': trip['start_location'],
                    'end_location': trip['end_location'],
                    'detection_method': 'gps_tracking'
                }
            }
            entries.append(entry)
        
        return entries
    
    def suggest_transport_mode_corrections(self, trip: Dict) -> List[Dict]:
        """Suggest alternative transport modes for manual correction"""
        suggestions = []
        
        distance_km = trip['distance_km']
        avg_speed = trip['avg_speed_kmh']
        
        # Generate plausible alternatives based on distance and speed
        if distance_km < 2:
            suggestions.append({
                'mode': 'walking',
                'probability': 0.8 if avg_speed < 6 else 0.2,
                'reason': 'Short distance, typical for walking'
            })
        
        if distance_km < 10 and avg_speed < 25:
            suggestions.append({
                'mode': 'cycling',
                'probability': 0.7 if 8 < avg_speed < 20 else 0.3,
                'reason': 'Distance and speed suitable for cycling'
            })
        
        if distance_km > 1:
            suggestions.append({
                'mode': 'car_petrol',
                'probability': 0.6 if avg_speed > 20 else 0.3,
                'reason': 'Most common motorized transport'
            })
            
            suggestions.append({
                'mode': 'bus',
                'probability': 0.4 if 15 < avg_speed < 40 else 0.2,
                'reason': 'Public transport option'
            })
        
        if distance_km > 50:
            suggestions.append({
                'mode': 'train',
                'probability': 0.5 if avg_speed > 40 else 0.2,
                'reason': 'Long distance, suitable for rail'
            })
        
        if distance_km > 200:
            suggestions.append({
                'mode': 'flight_domestic',
                'probability': 0.7 if avg_speed > 200 else 0.1,
                'reason': 'Very long distance, likely flight'
            })
        
        # Sort by probability
        suggestions.sort(key=lambda x: x['probability'], reverse=True)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def export_location_data(self, start_date: datetime = None, end_date: datetime = None) -> Dict:
        """Export location tracking data for external analysis"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()
        
        # Filter location history
        filtered_history = [
            point for point in self.location_history
            if start_date <= point['timestamp'] <= end_date
        ]
        
        # Detect trips
        trips = self.detect_trips()
        filtered_trips = [
            trip for trip in trips
            if start_date <= trip['start_time'] <= end_date
        ]
        
        # Generate summary
        summary = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'location_points': len(filtered_history),
            'trips_detected': len(filtered_trips),
            'total_distance_km': sum(trip['distance_km'] for trip in filtered_trips),
            'total_emissions_kg': sum(trip['carbon_footprint'] for trip in filtered_trips),
            'transport_mode_breakdown': {}
        }
        
        # Calculate transport mode breakdown
        for trip in filtered_trips:
            mode = trip['detected_transport_mode']
            if mode not in summary['transport_mode_breakdown']:
                summary['transport_mode_breakdown'][mode] = {
                    'trips': 0,
                    'distance_km': 0,
                    'emissions_kg': 0
                }
            
            summary['transport_mode_breakdown'][mode]['trips'] += 1
            summary['transport_mode_breakdown'][mode]['distance_km'] += trip['distance_km']
            summary['transport_mode_breakdown'][mode]['emissions_kg'] += trip['carbon_footprint']
        
        return {
            'summary': summary,
            'location_history': filtered_history,
            'trips': filtered_trips,
            'emission_entries': self.convert_trips_to_emission_entries(filtered_trips)
        } 