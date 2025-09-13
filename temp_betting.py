# Corrected get_sports_data method for BettingAgent
# This version handles the nested data structure returned by OvertimeService

def get_sports_data(self) -> List[Dict]:
    """
    Fetch and process sports data from OvertimeService.
    
    Returns:
        List[Dict]: List of processed game data
    """
    try:
        # Get raw data from OvertimeService
        raw_response = self.overtime_service.get_sports_data()
        
        if not raw_response:
            print("No data available from OvertimeService")
            return []
        
        # Initialize the list to store processed games
        processed_games = []
        
        # Handle the nested data structure: {"data": [{"markets": [...]}]}
        if isinstance(raw_response, dict):
            # Check if response has "data" key
            if "data" in raw_response:
                data_array = raw_response["data"]
                
                # Check if data is a list
                if isinstance(data_array, list):
                    # Iterate through data items
                    for data_item in data_array:
                        if isinstance(data_item, dict) and "markets" in data_item:
                            # Extract markets from the data item
                            markets = data_item["markets"]
                            
                            if isinstance(markets, list):
                                # Process each market
                                for market in markets:
                                    if self._is_valid_market(market):
                                        processed_game = self._process_market(market)
                                        if processed_game:
                                            processed_games.append(processed_game)
                            else:
                                print(f"WARNING: 'markets' is not a list, it's a {type(markets)}")
                        else:
                            print(f"WARNING: Data item missing 'markets' key or not a dict: {type(data_item)}")
                else:
                    print(f"WARNING: 'data' is not a list, it's a {type(data_array)}")
            
            # Alternative structure: direct dict with market categories
            else:
                # If it's a dict with categories, iterate through values()
                for key, markets in raw_response.items():
                    if isinstance(markets, list):
                        for market in markets:
                            if self._is_valid_market(market):
                                processed_game = self._process_market(market)
                                if processed_game:
                                    processed_games.append(processed_game)
        
        # Handle if raw_response is directly a list
        elif isinstance(raw_response, list):
            # Process as a direct list of markets
            for market in raw_response:
                if self._is_valid_market(market):
                    processed_game = self._process_market(market)
                    if processed_game:
                        processed_games.append(processed_game)
        
        # Handle unexpected structure
        else:
            print(f"WARNING: Unexpected response type: {type(raw_response)}")
            print(f"Response structure: {json.dumps(raw_response, indent=2)[:500]}...")  # Print first 500 chars
            
            # Attempt to extract any useful data
            if hasattr(raw_response, '__iter__'):
                try:
                    # Try to iterate through the response
                    for item in raw_response:
                        if isinstance(item, dict) and self._is_valid_market(item):
                            processed_game = self._process_market(item)
                            if processed_game:
                                processed_games.append(processed_game)
                except Exception as e:
                    print(f"ERROR: Failed to iterate through response: {e}")
        
        # Log the results
        if processed_games:
            print(f"--- Successfully processed {len(processed_games)} valid games from Overtime API ---")
        else:
            print("--- WARNING: No valid games found after processing ---")
            # Log more details about the raw response for debugging
            if isinstance(raw_response, dict):
                print(f"Raw response keys: {list(raw_response.keys())[:10]}")  # First 10 keys
            elif isinstance(raw_response, list):
                print(f"Raw response length: {len(raw_response)}")
        
        return processed_games
        
    except Exception as e:
        print(f"ERROR in get_sports_data: {e}")
        import traceback
        traceback.print_exc()
        return []
