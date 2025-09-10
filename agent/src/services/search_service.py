"""
Temporary Search Service for geolocation using DuckDuckGo search.
This is a Phase A isolated implementation for review.
"""

import requests
import re
from typing import Dict, Optional, List, Any
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for searching team information and finding home cities using DuckDuckGo.
    """
    
    def __init__(self):
        """Initialize the SearchService with search configuration."""
        self.base_url = "https://api.duckduckgo.com/"
        self.search_url = "https://duckduckgo.com/html/"
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        
        # Common team keywords for better search results
        self.team_keywords = [
            "home city", "stadium", "headquarters", "based in", "located in",
            "plays in", "home ground", "venue", "arena"
        ]
    
    def search_team_home_city(self, team_name: str) -> Optional[Dict[str, Any]]:
        """
        Search for a team's home city using DuckDuckGo.
        
        Args:
            team_name (str): Name of the team (e.g., "Real Madrid")
            
        Returns:
            Optional[Dict[str, Any]]: Team location information or None if failed
        """
        try:
            # Create search queries with different approaches
            search_queries = [
                f'"{team_name}" home city',
                f'"{team_name}" stadium location',
                f'"{team_name}" based in',
                f'"{team_name}" plays in',
                f'"{team_name}" headquarters'
            ]
            
            results = []
            
            for query in search_queries:
                result = self._perform_search(query)
                if result:
                    results.append(result)
            
            # Process and combine results
            if results:
                return self._process_search_results(team_name, results)
            
            logger.warning(f"No search results found for team: {team_name}")
            return None
            
        except Exception as e:
            logger.error(f"Search failed for team {team_name}: {str(e)}")
            return None
    
    def _perform_search(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Perform a single search query.
        
        Args:
            query (str): Search query string
            
        Returns:
            Optional[Dict[str, Any]]: Raw search result or None if failed
        """
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            params = {
                'q': query,
                'kl': 'us-en',  # Language preference
                'kp': '1'       # Safe search off
            }
            
            response = requests.get(
                self.search_url, 
                params=params, 
                headers=headers, 
                timeout=15
            )
            response.raise_for_status()
            
            return {
                'query': query,
                'content': response.text,
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for query '{query}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in search for '{query}': {str(e)}")
            return None
    
    def _process_search_results(self, team_name: str, results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Process and extract location information from search results.
        
        Args:
            team_name (str): Original team name
            results (List[Dict[str, Any]]): List of search results
            
        Returns:
            Optional[Dict[str, Any]]: Processed location information
        """
        try:
            # Common city patterns and keywords
            city_patterns = [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:City|Stadium|Arena|Ground)',
                r'\b(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*[A-Z]{2,3}',  # City, Country
                r'\b(?:based in|located in|headquartered in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            ]
            
            # Common European cities for football teams
            european_cities = [
                'Madrid', 'Barcelona', 'London', 'Manchester', 'Liverpool', 'Paris',
                'Milan', 'Rome', 'Munich', 'Berlin', 'Amsterdam', 'Lisbon', 'Porto',
                'Athens', 'Istanbul', 'Moscow', 'Kiev', 'Warsaw', 'Prague', 'Vienna'
            ]
            
            extracted_locations = []
            
            for result in results:
                content = result.get('content', '').lower()
                
                # Look for city mentions
                for pattern in city_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    for match in matches:
                        if isinstance(match, tuple):
                            match = ' '.join(match)
                        if match and len(match) > 2:
                            extracted_locations.append(match.strip())
                
                # Look for European cities specifically
                for city in european_cities:
                    if city.lower() in content:
                        extracted_locations.append(city)
            
            # Remove duplicates and filter results
            unique_locations = list(set(extracted_locations))
            filtered_locations = [
                loc for loc in unique_locations 
                if len(loc) > 2 and not any(word in loc.lower() for word in ['team', 'club', 'football', 'soccer'])
            ]
            
            if filtered_locations:
                # Try to determine the most likely home city
                home_city = self._determine_home_city(team_name, filtered_locations)
                
                return {
                    'team_name': team_name,
                    'home_city': home_city,
                    'possible_locations': filtered_locations[:5],  # Top 5 possibilities
                    'confidence': 'high' if home_city else 'medium',
                    'search_queries_used': [r['query'] for r in results]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to process search results: {str(e)}")
            return None
    
    def _determine_home_city(self, team_name: str, locations: List[str]) -> Optional[str]:
        """
        Determine the most likely home city from extracted locations.
        
        Args:
            team_name (str): Name of the team
            locations (List[str]): List of possible locations
            
        Returns:
            Optional[str]: Most likely home city or None
        """
        try:
            # Common team-city mappings
            team_city_mappings = {
                'real madrid': 'madrid',
                'barcelona': 'barcelona',
                'manchester united': 'manchester',
                'manchester city': 'manchester',
                'liverpool': 'liverpool',
                'arsenal': 'london',
                'chelsea': 'london',
                'tottenham': 'london',
                'bayern munich': 'munich',
                'borussia dortmund': 'dortmund',
                'ac milan': 'milan',
                'inter milan': 'milan',
                'juventus': 'turin',
                'paris saint-germain': 'paris',
                'ajax': 'amsterdam',
                'benfica': 'lisbon',
                'porto': 'porto',
                'olympiacos': 'athens',
                'galatasaray': 'istanbul',
                'dinamo kiev': 'kiev',
                'spartak moscow': 'moscow'
            }
            
            # Check exact mappings first
            team_lower = team_name.lower()
            if team_lower in team_city_mappings:
                return team_city_mappings[team_lower]
            
            # Check partial matches
            for team, city in team_city_mappings.items():
                if team in team_lower or team_lower in team:
                    return city
            
            # If no mapping found, return the first location that looks like a city
            for location in locations:
                if any(city.lower() in location.lower() for city in ['madrid', 'barcelona', 'london', 'paris', 'milan', 'munich']):
                    return location
            
            # Return the first location if available
            return locations[0] if locations else None
            
        except Exception as e:
            logger.error(f"Failed to determine home city: {str(e)}")
            return None
    
    def get_team_location_summary(self, team_name: str) -> Optional[str]:
        """
        Get a human-readable summary of team location.
        
        Args:
            team_name (str): Name of the team
            
        Returns:
            Optional[str]: Formatted location summary or None if failed
        """
        location_info = self.search_team_home_city(team_name)
        
        if not location_info:
            return None
        
        try:
            home_city = location_info.get('home_city', 'Unknown')
            confidence = location_info.get('confidence', 'unknown')
            
            summary = (
                f"Team: {team_name}\n"
                f"Home City: {home_city}\n"
                f"Confidence: {confidence.capitalize()}\n"
                f"Other possible locations: {', '.join(location_info.get('possible_locations', [])[:3])}"
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to create location summary: {str(e)}")
            return None
    
    def search_multiple_teams(self, team_names: List[str]) -> Dict[str, Any]:
        """
        Search for multiple teams' locations at once.
        
        Args:
            team_names (List[str]): List of team names to search
            
        Returns:
            Dict[str, Any]: Results for all teams
        """
        results = {}
        
        for team_name in team_names:
            logger.info(f"Searching for team: {team_name}")
            location_info = self.search_team_home_city(team_name)
            results[team_name] = location_info
        
        return results


# Example usage and testing
if __name__ == "__main__":
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Initialize service
    search_service = SearchService()
    
    # Test teams
    test_teams = [
        "Real Madrid",
        "Manchester United", 
        "Barcelona",
        "Bayern Munich"
    ]
    
    print("=== Team Location Search Test ===\n")
    
    for team in test_teams:
        print(f"--- Searching for {team} ---")
        
        # Get location info
        location = search_service.search_team_home_city(team)
        if location:
            print(f"Home City: {location.get('home_city', 'Unknown')}")
            print(f"Confidence: {location.get('confidence', 'Unknown')}")
            print(f"Possible locations: {location.get('possible_locations', [])}")
        else:
            print("No location found")
        
        # Get summary
        summary = search_service.get_team_location_summary(team)
        if summary:
            print(f"Summary:\n{summary}")
        
        print()
    
    # Test multiple teams search
    print("=== Multiple Teams Search ===")
    all_results = search_service.search_multiple_teams(test_teams)
    
    for team, result in all_results.items():
        if result:
            print(f"{team}: {result.get('home_city', 'Unknown')}")
        else:
            print(f"{team}: Not found")
