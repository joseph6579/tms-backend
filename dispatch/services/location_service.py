from typing import Dict, Optional
import json
from redis import Redis
from django.conf import settings

class LocationService:
    def __init__(self):
        self.redis = Redis(
            host=settings.REDISHOST,
            port=settings.REDISPORT,
            db=0,
            decode_responses=True
        )
        self.LOCATION_KEY_PREFIX = "driver_location:"
        self.LOCATION_TTL = 300  # 5 minutes

    def update_driver_location(self, driver_id: str, latitude: float, longitude: float) -> bool:
        """
        Update driver's location in Redis
        Returns True if successful, False otherwise
        """
        try:
            key = f"{self.LOCATION_KEY_PREFIX}{driver_id}"
            location_data = {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": import time; time.time()
            }
            
            # Store location data with TTL
            return self.redis.setex(
                key,
                self.LOCATION_TTL,
                json.dumps(location_data)
            )
        except Exception as e:
            print(f"Error updating location: {e}")
            return False

    def get_driver_location(self, driver_id: str) -> Optional[Dict]:
        """
        Get driver's location from Redis
        Returns location data if found, None otherwise
        """
        try:
            key = f"{self.LOCATION_KEY_PREFIX}{driver_id}"
            location_data = self.redis.get(key)
            
            if location_data:
                return json.loads(location_data)
            return None
        except Exception as e:
            print(f"Error getting location: {e}")
            return None

    def get_nearby_drivers(self, latitude: float, longitude: float, radius_km: float) -> list:
        """
        Get all drivers within specified radius
        Returns list of driver IDs and their locations
        """
        try:
            # Get all driver locations
            keys = self.redis.keys(f"{self.LOCATION_KEY_PREFIX}*")
            nearby_drivers = []

            for key in keys:
                location_data = self.redis.get(key)
                if location_data:
                    location = json.loads(location_data)
                    distance = self.calculate_distance(
                        latitude,
                        longitude,
                        location["latitude"],
                        location["longitude"]
                    )
                    
                    if distance <= radius_km:
                        driver_id = key.replace(self.LOCATION_KEY_PREFIX, "")
                        nearby_drivers.append({
                            "driver_id": driver_id,
                            "location": location,
                            "distance": distance
                        })

            return sorted(nearby_drivers, key=lambda x: x["distance"])
        except Exception as e:
            print(f"Error getting nearby drivers: {e}")
            return []

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points using Haversine formula
        Returns distance in kilometers
        """
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Earth's radius in kilometers

        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c

    def clear_driver_location(self, driver_id: str) -> bool:
        """
        Remove driver's location from Redis
        Returns True if successful, False otherwise
        """
        try:
            key = f"{self.LOCATION_KEY_PREFIX}{driver_id}"
            return bool(self.redis.delete(key))
        except Exception as e:
            print(f"Error clearing location: {e}")
            return False