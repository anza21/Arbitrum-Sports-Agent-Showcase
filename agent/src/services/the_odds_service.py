"""
Temporary TheOddsService implementation for inspection.
This service handles sports odds data from The Odds API with smart quota management.
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TheOddsService:
    """
    Service for fetching sports odds data from The Odds API.
    Implements smart quota management and test mode functionality.
    """
    
    def __init__(self, api_key: Optional[str] = None, test_mode: bool = True):
        """
        Initialize the TheOddsService.
        
        Args:
            api_key: API key for The Odds API. If None, will try to get from environment.
            test_mode: If True, enables test mode with reduced API calls and mock data fallback.
        """
        self.api_key = api_key or os.getenv('THE_ODDS_API_KEY')
        self.test_mode = test_mode
        self.base_url = "https://api.the-odds-api.com/v4"
        
        # Quota management
        self.requests_used = 0
        self.requests_remaining = 1000  # Default quota
        self.last_request_time = None
        self.rate_limit_delay = 1.0  # Seconds between requests
        
        # Test mode settings
        self.mock_data_enabled = test_mode
        self.max_test_requests = 10 if test_mode else 0
        
        if not self.api_key:
            logger.warning("No API key provided. Service will operate in test mode only.")
            self.test_mode = True
            self.mock_data_enabled = True
    
    def _check_quota(self) -> bool:
        """
        Check if we have remaining API quota.
        
        Returns:
            bool: True if quota available, False otherwise
        """
        if self.test_mode and self.requests_used >= self.max_test_requests:
            logger.info(f"Test mode: Max requests ({self.max_test_requests}) reached. Using mock data.")
            return False
        
        if self.requests_remaining <= 0:
            logger.warning("API quota exhausted. No more requests available.")
            return False
        
        return True
    
    def _handle_rate_limiting(self):
        """Handle rate limiting by adding delays between requests."""
        if self.last_request_time:
            time_since_last = time.time() - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                sleep_time = self.rate_limit_delay - time_since_last
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _update_quota_from_headers(self, response: requests.Response):
        """Update quota information from API response headers."""
        if 'x-requests-used' in response.headers:
            self.requests_used = int(response.headers['x-requests-used'])
        
        if 'x-requests-remaining' in response.headers:
            self.requests_remaining = int(response.headers['x-requests-remaining'])
        
        logger.info(f"Quota: {self.requests_used} used, {self.requests_remaining} remaining")
    
    def _get_mock_odds_data(self, sport_key: str) -> List[Dict[str, Any]]:
        """
        Generate mock odds data for testing purposes.
        
        Args:
            sport_key: The sport key for which to generate mock data
            
        Returns:
            List of mock odds data
        """
        mock_data = [
            {
                "id": f"mock_{sport_key}_1",
                "sport_key": sport_key,
                "sport_title": f"Mock {sport_key.title()}",
                "commence_time": (datetime.now() + timedelta(hours=2)).isoformat(),
                "home_team": "Home Team",
                "away_team": "Away Team",
                "bookmakers": [
                    {
                        "key": "mock_bookie",
                        "title": "Mock Bookmaker",
                        "last_update": datetime.now().isoformat(),
                        "markets": [
                            {
                                "key": "h2h",
                                "last_update": datetime.now().isoformat(),
                                "outcomes": [
                                    {"name": "Home Team", "price": 2.0},
                                    {"name": "Away Team", "price": 1.8}
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
        
        logger.info(f"Generated mock data for {sport_key}")
        return mock_data
    
    def get_sports_odds(
        self, 
        sport_key: str, 
        regions: str = 'us,eu', 
        markets: str = 'h2h', 
        odds_format: str = 'decimal'
    ) -> List[Dict[str, Any]]:
        """
        Fetch sports odds for a specific sport.
        
        Args:
            sport_key: The sport key (e.g., 'soccer_epl', 'basketball_nba')
            regions: Comma-separated list of regions (default: 'us,eu')
            markets: Comma-separated list of markets (default: 'h2h')
            odds_format: Odds format (default: 'decimal')
            
        Returns:
            List of odds data for the specified sport
        """
        if not self._check_quota():
            if self.mock_data_enabled:
                return self._get_mock_odds_data(sport_key)
            else:
                logger.error("No quota available and mock data disabled")
                return []
        
        self._handle_rate_limiting()
        
        # Build the API endpoint
        endpoint = f"{self.base_url}/sports/{sport_key}/odds"
        
        # Prepare query parameters
        params = {
            'apiKey': self.api_key,
            'regions': regions,
            'markets': markets,
            'oddsFormat': odds_format
        }
        
        try:
            logger.info(f"Fetching odds for {sport_key} from {endpoint}")
            response = requests.get(endpoint, params=params, timeout=30)
            
            # Update quota information
            self._update_quota_from_headers(response)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched {len(data)} odds records for {sport_key}")
                return data
            elif response.status_code == 401:
                logger.error("API key invalid or expired")
                return []
            elif response.status_code == 429:
                logger.error("Rate limit exceeded")
                return []
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if self.mock_data_enabled:
                logger.info("Falling back to mock data due to request failure")
                return self._get_mock_odds_data(sport_key)
            return []
    
    def get_available_sports(self) -> List[Dict[str, Any]]:
        """
        Get list of available sports.
        
        Returns:
            List of available sports
        """
        if not self._check_quota():
            if self.mock_data_enabled:
                return [
                    {"key": "soccer_epl", "title": "English Premier League", "description": "Mock soccer data"},
                    {"key": "basketball_nba", "title": "NBA", "description": "Mock basketball data"},
                    {"key": "american_football_nfl", "title": "NFL", "description": "Mock football data"}
                ]
            else:
                return []
        
        self._handle_rate_limiting()
        
        endpoint = f"{self.base_url}/sports"
        params = {'apiKey': self.api_key}
        
        try:
            logger.info("Fetching available sports")
            response = requests.get(endpoint, params=params, timeout=30)
            
            self._update_quota_from_headers(response)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Successfully fetched {len(data)} available sports")
                return data
            else:
                logger.error(f"Failed to fetch sports: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            if self.mock_data_enabled:
                return [
                    {"key": "soccer_epl", "title": "English Premier League", "description": "Mock soccer data"},
                    {"key": "basketball_nba", "title": "NBA", "description": "Mock basketball data"},
                    {"key": "american_football_nfl", "title": "NFL", "description": "Mock football data"}
                ]
            return []
    
    def get_quota_status(self) -> Dict[str, Any]:
        """
        Get current quota status.
        
        Returns:
            Dictionary with quota information
        """
        return {
            'requests_used': self.requests_used,
            'requests_remaining': self.requests_remaining,
            'test_mode': self.test_mode,
            'mock_data_enabled': self.mock_data_enabled,
            'max_test_requests': self.max_test_requests
        }
    
    def reset_quota(self):
        """Reset quota counters (useful for testing)."""
        self.requests_used = 0
        self.requests_remaining = 1000
        self.last_request_time = None
        logger.info("Quota counters reset")
    
    def set_test_mode(self, enabled: bool, max_requests: int = 10):
        """
        Configure test mode settings.
        
        Args:
            enabled: Whether to enable test mode
            max_requests: Maximum number of API requests in test mode
        """
        self.test_mode = enabled
        self.mock_data_enabled = enabled
        self.max_test_requests = max_requests if enabled else 0
        logger.info(f"Test mode {'enabled' if enabled else 'disabled'} with max {max_requests} requests")


# Example usage and testing
if __name__ == "__main__":
    # Initialize service (will use environment variable if available)
    service = TheOddsService(test_mode=True)
    
    # Get quota status
    print("Initial quota status:", service.get_quota_status())
    
    # Test getting available sports
    sports = service.get_available_sports()
    print(f"Available sports: {len(sports)}")
    
    # Test getting odds for a specific sport
    if sports:
        first_sport = sports[0]['key']
        odds = service.get_sports_odds(first_sport)
        print(f"Odds for {first_sport}: {len(odds)} records")
    
    # Final quota status
    print("Final quota status:", service.get_quota_status())
