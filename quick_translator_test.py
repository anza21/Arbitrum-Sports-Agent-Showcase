#!/usr/bin/env python3
"""
QUICK TRANSLATOR TEST
Άμεση δοκιμή του νέου translator fix για να αποδείξω ότι δουλεύει
"""

# Mock data για τεστ
mock_llm_decisions = [
    {'market_id': '3', 'teams': 'Penn State vs Florida International', 'position': 0, 'confidence': 0.80},
    {'market_id': '4', 'teams': 'Syracuse vs Connecticut', 'position': 0, 'confidence': 0.78},
    {'market_id': '6', 'teams': 'Jacksonville State vs Liberty', 'position': 1, 'confidence': 0.72},
    {'market_id': '7', 'teams': 'SMU vs Baylor', 'position': 1, 'confidence': 0.65},
    {'market_id': '53', 'teams': 'Wofford vs Richmond', 'position': 1, 'confidence': 0.70}
]

mock_processed_games = [
    {'homeTeam': 'Penn State', 'awayTeam': 'Florida International', 'gameId': '0x1111111111111111', 'type': 'winner'},
    {'homeTeam': 'Syracuse', 'awayTeam': 'Connecticut', 'gameId': '0x2222222222222222', 'type': 'winner'},
    {'homeTeam': 'Jacksonville State', 'awayTeam': 'Liberty', 'gameId': '0x3333333333333333', 'type': 'winner'},
    {'homeTeam': 'SMU', 'awayTeam': 'Baylor', 'gameId': '0x4444444444444444', 'type': 'winner'},
    {'homeTeam': 'Wofford', 'awayTeam': 'Richmond', 'gameId': '0x5555555555555555', 'type': 'winner'},
    {'homeTeam': 'Indiana', 'awayTeam': 'Kennesaw State', 'gameId': '0x6666666666666666', 'type': 'winner'},
]

def smart_translator_test():
    """Test του νέου smart translator logic"""
    print("🚀 SMART TRANSLATOR TEST STARTING...")
    print(f"📊 LLM Decisions: {len(mock_llm_decisions)}")
    print(f"📊 Available Games: {len(mock_processed_games)}")
    print()
    
    strategic_games = []
    
    for decision in mock_llm_decisions:
        teams = decision['teams']
        market_id = decision['market_id']
        matching_game = None
        
        print(f"🔍 Processing: {teams}")
        
        # 🚀 SMART TRANSLATOR: Find unique game by exact team match
        for game in mock_processed_games:
            home_team = game.get('homeTeam', '').strip().lower()
            away_team = game.get('awayTeam', '').strip().lower()
            teams_normalized = teams.strip().lower()
            
            # Create exact match patterns for both directions
            forward_match = f"{home_team} vs {away_team}"
            reverse_match = f"{away_team} vs {home_team}"
            
            # Only match if EXACT team combination matches
            if teams_normalized == forward_match or teams_normalized == reverse_match:
                # Prefer winner/moneyline markets over other types for main betting
                if game.get('type') == 'winner' or 'winner' in game.get('type', '').lower():
                    matching_game = game.copy()
                    decision['market_id'] = game.get('gameId', game.get('game_id', ''))
                    print(f"🎯 EXACT MATCH: '{teams}' → {decision['market_id'][:20]}... (winner market)")
                    break
                elif not matching_game:  # Fallback to any market type if no winner found
                    matching_game = game.copy()
                    decision['market_id'] = game.get('gameId', game.get('game_id', ''))
                    print(f"🔄 FALLBACK MATCH: '{teams}' → {decision['market_id'][:20]}... ({game.get('type', 'unknown')})")
                    # Don't break here, keep looking for winner market
        
        if matching_game:
            # Add LLM decision data to the game
            matching_game['llm_position'] = decision.get('position', 0)
            matching_game['llm_confidence'] = decision.get('confidence', 0.5)
            matching_game['llm_reasoning'] = decision.get('reasoning', '')
            matching_game['real_market_id'] = decision['market_id']  # Store the translated ID
            
            # 🚀 DEDUPLICATION: Ensure we don't add duplicate games
            game_signature = f"{matching_game.get('homeTeam', 'Unknown')} vs {matching_game.get('awayTeam', 'Unknown')}"
            if not any(f"{g.get('homeTeam', 'Unknown')} vs {g.get('awayTeam', 'Unknown')}" == game_signature for g in strategic_games):
                strategic_games.append(matching_game)
                print(f"✅ UNIQUE LLM Decision: {decision.get('teams', 'Unknown')} - Position: {decision.get('position')} - Confidence: {decision.get('confidence')}")
            else:
                print(f"⚠️ DUPLICATE SKIPPED: {decision.get('teams', 'Unknown')} already in selection")
        else:
            print(f"❌ NO MATCH FOUND: {teams}")
        print()
    
    # 🚀 VOLUME STRATEGY: Use ALL unique LLM decisions (remove artificial limit)
    valid_games = strategic_games  # Use ALL strategic games, not just first 5
    print(f"✅ Using {len(valid_games)} LLM-selected games for betting")
    
    print("\n🎯 FINAL RESULTS:")
    for i, game in enumerate(valid_games, 1):
        print(f"{i}. {game.get('homeTeam')} vs {game.get('awayTeam')} - Position: {game.get('llm_position')} - Confidence: {game.get('llm_confidence')}")
    
    return valid_games

if __name__ == "__main__":
    results = smart_translator_test()
    print(f"\n🏆 SUCCESS: {len(results)} unique games selected with new translator!")
