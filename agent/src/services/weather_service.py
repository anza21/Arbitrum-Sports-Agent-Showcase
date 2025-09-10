"""
Temporary Weather Service for OpenWeatherMap API integration.
This is a Phase A isolated implementation for review.
"""

import os
import requests
from typing import Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """
    Service for fetching weather data from OpenWeatherMap API.
    """
    
    def __init__(self):
        """Initialize the WeatherService with API configuration."""
        self.api_key = os.getenv('OPENWEATHERMAP_API_KEY')
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
        
        if not self.api_key:
            logger.warning("OPENWEATHERMAP_API_KEY not found in environment variables")
    
    def get_weather_by_city(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data for a given city name.
        
        Args:
            city_name (str): Name of the city to get weather for
            
        Returns:
            Optional[Dict[str, Any]]: Weather data or None if failed
        """
        if not self.api_key:
            logger.error("Cannot fetch weather: API key not configured")
            return None
        
        try:
            params = {
                'q': city_name,
                'appid': self.api_key,
                'units': 'metric'  # Use Celsius for temperature
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            weather_data = response.json()
            
            # Extract relevant weather information
            processed_data = {
                'city': weather_data.get('name'),
                'country': weather_data.get('sys', {}).get('country'),
                'temperature': {
                    'current': weather_data.get('main', {}).get('temp'),
                    'feels_like': weather_data.get('main', {}).get('feels_like'),
                    'min': weather_data.get('main', {}).get('temp_min'),
                    'max': weather_data.get('main', {}).get('temp_max')
                },
                'humidity': weather_data.get('main', {}).get('humidity'),
                'pressure': weather_data.get('main', {}).get('pressure'),
                'weather_description': weather_data.get('weather', [{}])[0].get('description'),
                'weather_main': weather_data.get('weather', [{}])[0].get('main'),
                'wind': {
                    'speed': weather_data.get('wind', {}).get('speed'),
                    'direction': weather_data.get('wind', {}).get('deg')
                },
                'rain': {
                    '1h': weather_data.get('rain', {}).get('1h', 0),
                    '3h': weather_data.get('rain', {}).get('3h', 0)
                },
                'snow': {
                    '1h': weather_data.get('snow', {}).get('1h', 0),
                    '3h': weather_data.get('snow', {}).get('3h', 0)
                },
                'clouds': weather_data.get('clouds', {}).get('all'),
                'visibility': weather_data.get('visibility'),
                'timestamp': weather_data.get('dt'),
                'sunrise': weather_data.get('sys', {}).get('sunrise'),
                'sunset': weather_data.get('sys', {}).get('sunset')
            }
            
            logger.info(f"Successfully fetched weather data for {city_name}")
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {city_name}: {str(e)}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Failed to parse weather data for {city_name}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather for {city_name}: {str(e)}")
            return None
    
    def get_weather_summary(self, city_name: str) -> Optional[str]:
        """
        Get a human-readable weather summary for a city.
        
        Args:
            city_name (str): Name of the city
            
        Returns:
            Optional[str]: Formatted weather summary or None if failed
        """
        weather_data = self.get_weather_by_city(city_name)
        
        if not weather_data:
            return None
        
        try:
            temp = weather_data['temperature']['current']
            description = weather_data['weather_description']
            humidity = weather_data['humidity']
            wind_speed = weather_data['wind']['speed']
            
            summary = (
                f"Weather in {weather_data['city']}, {weather_data['country']}: "
                f"{temp}°C, {description}. "
                f"Humidity: {humidity}%, Wind: {wind_speed} m/s"
            )
            
            return summary
            
        except KeyError as e:
            logger.error(f"Failed to create weather summary: {str(e)}")
            return None
    
    def is_weather_suitable_for_sports(self, city_name: str) -> Optional[Dict[str, Any]]:
        """
        Check if weather conditions are suitable for outdoor sports.
        
        Args:
            city_name (str): Name of the city
            
        Returns:
            Optional[Dict[str, Any]]: Suitability assessment or None if failed
        """
        weather_data = self.get_weather_by_city(city_name)
        
        if not weather_data:
            return None
        
        try:
            temp = weather_data['temperature']['current']
            rain_1h = weather_data['rain']['1h']
            wind_speed = weather_data['wind']['speed']
            visibility = weather_data['visibility']
            
            # Define thresholds for sports suitability
            suitable_temp = -5 <= temp <= 35  # Celsius
            suitable_rain = rain_1h < 5  # mm per hour
            suitable_wind = wind_speed < 15  # m/s
            suitable_visibility = visibility > 5000  # meters
            
            overall_suitable = all([
                suitable_temp, suitable_rain, suitable_wind, suitable_visibility
            ])
            
            assessment = {
                'city': weather_data['city'],
                'overall_suitable': overall_suitable,
                'temperature_suitable': suitable_temp,
                'rain_suitable': suitable_rain,
                'wind_suitable': suitable_wind,
                'visibility_suitable': suitable_visibility,
                'details': {
                    'temperature': f"{temp}°C",
                    'rain_1h': f"{rain_1h} mm/h",
                    'wind_speed': f"{wind_speed} m/s",
                    'visibility': f"{visibility} m"
                }
            }
            
            return assessment
            
        except KeyError as e:
            logger.error(f"Failed to assess weather suitability: {str(e)}")
            return None


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize service
    weather_service = WeatherService()
    
    # Test cities
    test_cities = ["London", "Madrid", "Barcelona", "Milan"]
    
    for city in test_cities:
        print(f"\n--- Weather for {city} ---")
        
        # Get full weather data
        weather = weather_service.get_weather_by_city(city)
        if weather:
            print(f"Temperature: {weather['temperature']['current']}°C")
            print(f"Description: {weather['weather_description']}")
            print(f"Wind: {weather['wind']['speed']} m/s")
        
        # Get suitability assessment
        suitability = weather_service.is_weather_suitable_for_sports(city)
        if suitability:
            print(f"Sports suitable: {suitability['overall_suitable']}")
        
        # Get summary
        summary = weather_service.get_weather_summary(city)
        if summary:
            print(f"Summary: {summary}")
