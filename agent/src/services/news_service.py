import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

class NewsService:
    """
    Service for fetching news related to sports teams and events.
    
    This service integrates with NewsAPI.org to retrieve relevant news articles
    that can influence betting decisions based on team performance, injuries,
    transfers, and other relevant factors.
    """
    
    def __init__(self):
        """Initialize the NewsService with API configuration."""
        load_dotenv()
        
        self.api_key = os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2/everything"
        self.timeout = 15
        self.language = "en"
        self.page_size = 5
        
        if not self.api_key:
            print("WARNING: NEWS_API_KEY not found in environment variables. NewsService will be disabled.")
    
    def get_news_for_team(self, team_name: str, language: str = 'en', page_size: int = 5):
        """
        Fetches recent news articles for a specific team name with graceful
        handling for rate limiting errors.
        """
        if not self.api_key:
            return [] # Return empty list if API key is not set

        try:
            params = {
                'q': team_name,
                'language': language,
                'pageSize': page_size,
                'sortBy': 'publishedAt',
                'apiKey': self.api_key
            }
            response = requests.get(self.base_url, params=params, timeout=15)
            response.raise_for_status()

            articles = response.json().get('articles', [])
            print(f"--- NewsService: Fetched {len(articles)} articles for '{team_name}'. ---")
            return articles

        except requests.exceptions.HTTPError as http_err:
            if http_err.response.status_code == 429:
                print(f"--- NewsService WARNING: Rate limit exceeded for NewsAPI. Continuing without news for '{team_name}'. ---")
                return [] # Return an empty list to allow agent to continue
            else:
                print(f"--- NewsService ERROR: HTTP error occurred for '{team_name}': {http_err} ---")
                return [] # Return empty list on other HTTP errors as well

        except requests.exceptions.RequestException as e:
            print(f"--- NewsService ERROR: Could not fetch news for '{team_name}': {e} ---")
            return [] # Return empty list for general request errors
    
    def _calculate_relevance_score(self, article: Dict, team_name: str) -> float:
        """
        Calculate relevance score for an article based on team name mentions.
        
        Args:
            article (Dict): Article data from NewsAPI
            team_name (str): Name of the team
            
        Returns:
            float: Relevance score (higher is more relevant)
        """
        score = 0.0
        
        # Check title relevance
        title = article.get('title', '').lower()
        if team_name.lower() in title:
            score += 3.0
        
        # Check description relevance
        description = article.get('description', '').lower()
        if team_name.lower() in description:
            score += 2.0
        
        # Check content relevance (if available)
        content = article.get('content', '').lower()
        if team_name.lower() in content:
            score += 1.0
        
        # Bonus for recent articles
        try:
            from datetime import datetime
            published_at = datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00'))
            hours_old = (datetime.now().astimezone() - published_at).total_seconds() / 3600
            if hours_old < 24:
                score += 1.0
            elif hours_old < 72:
                score += 0.5
        except:
            pass
        
        return score
    
    def get_news_summary(self, team_name: str, language: str = 'en', page_size: int = 5) -> Optional[str]:
        """
        Get a summary of news for a team.
        
        Args:
            team_name (str): Name of the team
            language (str): Language for news (default: 'en')
            page_size (int): Number of articles to fetch (default: 5)
            
        Returns:
            Optional[str]: Formatted news summary or None if no news
        """
        articles = self.get_news_for_team(team_name, language, page_size)
        
        if not articles:
            return None
        
        summary = f"📰 News Summary for {team_name}:\n\n"
        
        for i, article in enumerate(articles[:3], 1): # Top 3 articles
            summary += f"{i}. {article['title']}\n"
            summary += f"   📅 {article.get('publishedAt', '')[:10]}\n"
            summary += f"   📰 {article.get('source', {}).get('name', '')}\n"
            summary += f"   🔗 {article.get('url', '')}\n\n"
        
        return summary
    
    def is_service_available(self) -> bool:
        """
        Check if the NewsService is available (has API key).
        
        Returns:
            bool: True if service is available, False otherwise
        """
        return self.api_key is not None
