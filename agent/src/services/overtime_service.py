import requests
import json
import os

class OvertimeService:
    """
    A service to interact with the Overtime Protocol API v2.
    Handles fetching sports, markets, and placing bets.
    """
    API_BASE_URL = "https://api.overtime.io"

    def __init__(self):
        print("Overtime Service Initialized.")

    def get_sports_data(self):
        """
        Fetches all available sports markets from the Overtime API,
        including the necessary API key header for authentication.
        Enhanced to include liquidity and volume data extraction.
        """
        try:
            api_key = os.getenv("OVERTIME_REST_API_KEY")
            if not api_key:
                print("Error: OVERTIME_REST_API_KEY not found in environment variables.")
                return None

            endpoint = f"{self.API_BASE_URL}/overtime-v2/networks/42161/markets"
            headers = {
                "X-API-Key": api_key
            }

            # The network parameter is part of the URL, so params dict is not needed for this call.
            response = requests.get(endpoint, headers=headers)
            response.raise_for_status()  # Raises an HTTPError for bad responses

            response_data = response.json()
            
            # Extract markets from the response structure
            # The API returns: {"Football": {...}, "Soccer": {...}, "Basketball": {...}, ...}
            if isinstance(response_data, dict):
                all_games = []
                sports_processed = 0
                
                # Process each sport category
                for sport_name, sport_data in response_data.items():
                    if isinstance(sport_data, dict):
                        sports_processed += 1
                        # Each sport contains subcategories (league IDs) with lists of games
                        for league_id, games_list in sport_data.items():
                            if isinstance(games_list, list):
                                # Add sport name to each game for context and enhance with liquidity/volume data
                                for game in games_list:
                                    if isinstance(game, dict):
                                        # Add sport field if not present
                                        game['sport'] = sport_name
                                        
                                        # Enhance game data with liquidity and volume information
                                        enhanced_game = self._enhance_game_with_liquidity_volume_data(game)
                                        all_games.append(enhanced_game)
                
                if all_games:
                    print(f"Successfully fetched {len(all_games)} games/markets from {sports_processed} sports.")
                    print(f"Enhanced with liquidity and volume data extraction.")
                    
                    return all_games
                else:
                    print(f"No games found in {sports_processed} sports categories.")
            
            # Fallback: if the structure is different, return the raw response
            print(f"Unexpected response structure, returning raw data with {len(response_data) if isinstance(response_data, (list, dict)) else 0} items")
            return response_data
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching markets from Overtime API: {e}")
            return None

    def get_market_result(self, market_id: str):
        """
        Fetches the result for a specific, resolved market.
        """
        api_key = os.getenv("OVERTIME_REST_API_KEY")
        if not api_key:
            return None
        try:
            # Note: The endpoint for a single market might be different. This is a placeholder.
            # We assume a standard REST pattern.
            endpoint = f"{self.API_BASE_URL}/overtime-v2/networks/42161/markets/{market_id}"
            headers = {"X-API-Key": api_key}

            response = requests.get(endpoint, headers=headers, timeout=15)
            response.raise_for_status()

            market_data = response.json()
            if market_data.get('isResolved', False):
                print(f"--- OvertimeService: Fetched result for market {market_id}. ---")
                return {"winning_position": market_data.get("winningPosition")}
            return None # Market is not resolved yet

        except requests.exceptions.RequestException as e:
            print(f"--- OvertimeService ERROR: Could not fetch result for market {market_id}: {e} ---")
            return None

    def _enhance_game_with_liquidity_volume_data(self, game):
        """
        Enhances game data with liquidity and volume information.
        Extracts and calculates liquidity and volume metrics from available data.
        """
        enhanced_game = game.copy()
        
        # Initialize liquidity and volume fields
        enhanced_game['liquidity'] = None
        enhanced_game['volume'] = None
        enhanced_game['liquidity_metrics'] = {}
        enhanced_game['volume_metrics'] = {}
        
        try:
            # Extract liquidity indicators from existing data
            liquidity_indicators = self._extract_liquidity_indicators(game)
            enhanced_game['liquidity'] = liquidity_indicators.get('primary_liquidity')
            enhanced_game['liquidity_metrics'] = liquidity_indicators
            
            # Extract volume indicators from existing data
            volume_indicators = self._extract_volume_indicators(game)
            enhanced_game['volume'] = volume_indicators.get('primary_volume')
            enhanced_game['volume_metrics'] = volume_indicators
            
        except Exception as e:
            print(f"Warning: Could not extract liquidity/volume data for game {game.get('gameId', 'unknown')}: {e}")
        
        return enhanced_game
    
    def _extract_liquidity_indicators(self, game):
        """
        Extracts liquidity indicators from game data.
        Analyzes odds data and market status to infer liquidity levels.
        """
        liquidity_metrics = {
            'primary_liquidity': None,
            'odds_consistency': None,
            'market_depth': None,
            'spread_tightness': None
        }
        
        try:
            # Analyze odds data for liquidity indicators
            odds = game.get('odds', [])
            if odds and len(odds) >= 2:
                # Check if odds are consistent (non-zero values indicate active market)
                odds_values = [odd.get('decimal', 0) for odd in odds if odd.get('decimal', 0) > 0]
                
                if odds_values:
                    liquidity_metrics['odds_consistency'] = len(odds_values) / len(odds)
                    liquidity_metrics['primary_liquidity'] = sum(odds_values) / len(odds_values)
                    
                    # Calculate spread tightness (smaller spreads indicate higher liquidity)
                    if len(odds_values) >= 2:
                        spread = abs(odds_values[0] - odds_values[1])
                        liquidity_metrics['spread_tightness'] = 1.0 / (1.0 + spread)  # Higher value = tighter spread
            
            # Market status indicators
            is_open = game.get('isOpen', False)
            is_paused = game.get('isPaused', False)
            
            if is_open and not is_paused:
                liquidity_metrics['market_depth'] = 'active'
            elif is_paused:
                liquidity_metrics['market_depth'] = 'paused'
            else:
                liquidity_metrics['market_depth'] = 'inactive'
                
        except Exception as e:
            print(f"Warning: Error extracting liquidity indicators: {e}")
        
        return liquidity_metrics
    
    def _extract_volume_indicators(self, game):
        """
        Extracts volume indicators from game data.
        Analyzes market activity and betting patterns to infer volume levels.
        """
        volume_metrics = {
            'primary_volume': None,
            'market_activity': None,
            'position_complexity': None,
            'betting_intensity': None
        }
        
        try:
            # Analyze market activity based on status and type
            is_open = game.get('isOpen', False)
            market_type = game.get('type', '')
            status = game.get('status', 0)
            
            # Market activity score
            activity_score = 0
            if is_open:
                activity_score += 1
            if status == 0:  # Open status
                activity_score += 1
            if market_type in ['spread', 'total', 'moneyline']:  # Popular market types
                activity_score += 1
            
            volume_metrics['market_activity'] = activity_score
            volume_metrics['primary_volume'] = activity_score
            
            # Analyze position complexity (more positions = potentially higher volume)
            combined_positions = game.get('combinedPositions', [])
            if combined_positions:
                position_count = sum(len(pos) for pos in combined_positions if isinstance(pos, list))
                volume_metrics['position_complexity'] = position_count
                volume_metrics['betting_intensity'] = min(position_count / 10.0, 1.0)  # Normalize to 0-1
            
            # Check for player props (indicates specialized betting activity)
            is_player_props = game.get('isPlayerPropsMarket', False)
            if is_player_props:
                volume_metrics['betting_intensity'] = (volume_metrics.get('betting_intensity', 0) + 0.2)
                
        except Exception as e:
            print(f"Warning: Error extracting volume indicators: {e}")
        
        return volume_metrics

# Example usage for testing
if __name__ == '__main__':
    service = OvertimeService()
    available_markets = service.get_sports_data()
    if available_markets:
        # Print the first 2 markets for brevity
        print(json.dumps(available_markets[:2], indent=2))
