import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.article_clustering import article_clusterer
from app.summarization_service import summarization_service
from app.news_fetcher import fetch_multiple_pages
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class TLDRService:
    def __init__(self):
        """Initialize the TL;DR service."""
        self.news_api_key = os.getenv("NEWSAPI_KEY")
        self.cache = {}  # Simple in-memory cache
        self.cache_duration = timedelta(hours=1)  # Cache for 1 hour
    
    def get_category_tldr(self, category: str = "all", 
                         force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get TL;DR summary for a specific category.
        
        Args:
            category: News category (all, business, technology, etc.)
            force_refresh: Force refresh of cached data
            
        Returns:
            Dictionary with TL;DR information for the category
        """
        cache_key = f"tldr_{category}"
        current_time = datetime.now()
        
        # Check cache first
        if not force_refresh and cache_key in self.cache:
            cached_data, cache_time = self.cache[cache_key]
            if current_time - cache_time < self.cache_duration:
                logger.info(f"Returning cached TL;DR for category: {category}")
                return cached_data
        
        try:
            logger.info(f"Generating TL;DR for category: {category}")
            
            # Fetch articles for the category
            articles = fetch_multiple_pages(
                self.news_api_key, 
                category=category, 
                total_articles=100
            )
            
            if not articles:
                return {
                    "category": category,
                    "date": current_time.strftime("%Y-%m-%d"),
                    "total_clusters": 0,
                    "total_articles": 0,
                    "summaries": [],
                    "error": "No articles found"
                }
            
            # Cluster articles by topic
            clusters = article_clusterer.cluster_articles(
                articles,
                min_cluster_size=2,  # At least 2 articles per cluster
                max_clusters=8       # Maximum 8 clusters
            )
            
            # Create TL;DR summaries
            tldr_result = summarization_service.create_category_tldr(
                clusters,
                category,
                max_summaries=5
            )
            
            # Add timestamp
            tldr_result["generated_at"] = current_time.isoformat()
            tldr_result["date"] = current_time.strftime("%Y-%m-%d")
            
            # Cache the result
            self.cache[cache_key] = (tldr_result, current_time)
            
            logger.info(f"Generated TL;DR for {category}: {len(clusters)} clusters, {len(articles)} articles")
            return tldr_result
            
        except Exception as e:
            logger.error(f"Error generating TL;DR for category {category}: {e}")
            return {
                "category": category,
                "date": current_time.strftime("%Y-%m-%d"),
                "total_clusters": 0,
                "total_articles": 0,
                "summaries": [],
                "error": str(e)
            }
    
    def get_all_categories_tldr(self, categories: Optional[List[str]] = None,
                               force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get TL;DR summaries for all categories.
        
        Args:
            categories: List of categories to process (default: all available)
            force_refresh: Force refresh of cached data
            
        Returns:
            Dictionary with TL;DR information for all categories
        """
        if categories is None:
            categories = ["all", "business", "technology", "health", "science", "sports", "entertainment"]
        
        results = {}
        total_articles = 0
        total_clusters = 0
        
        for category in categories:
            try:
                category_result = self.get_category_tldr(category, force_refresh)
                results[category] = category_result
                
                total_articles += category_result.get("total_articles", 0)
                total_clusters += category_result.get("total_clusters", 0)
                
            except Exception as e:
                logger.error(f"Error processing category {category}: {e}")
                results[category] = {
                    "category": category,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "total_clusters": 0,
                    "total_articles": 0,
                    "summaries": [],
                    "error": str(e)
                }
        
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "generated_at": datetime.now().isoformat(),
            "total_categories": len(categories),
            "total_articles": total_articles,
            "total_clusters": total_clusters,
            "categories": results
        }
    
    def get_trending_topics(self, category: str = "all", 
                           min_cluster_size: int = 3) -> List[Dict[str, Any]]:
        """
        Get trending topics from a category based on cluster size and entities.
        
        Args:
            category: News category to analyze
            min_cluster_size: Minimum cluster size to consider trending
            
        Returns:
            List of trending topics with metadata
        """
        try:
            # Get fresh data for trending analysis
            category_result = self.get_category_tldr(category, force_refresh=True)
            
            trending_topics = []
            
            for summary in category_result.get("summaries", []):
                if summary.get("article_count", 0) >= min_cluster_size:
                    trending_topics.append({
                        "topic": summary.get("summary", ""),
                        "article_count": summary.get("article_count", 0),
                        "key_entities": summary.get("key_entities", []),
                        "rank": summary.get("rank", 0)
                    })
            
            # Sort by article count
            trending_topics.sort(key=lambda x: x["article_count"], reverse=True)
            
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error getting trending topics for {category}: {e}")
            return []
    
    def clear_cache(self):
        """Clear the TL;DR cache."""
        self.cache.clear()
        logger.info("TL;DR cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = datetime.now()
        active_entries = 0
        expired_entries = 0
        
        for cache_key, (_, cache_time) in self.cache.items():
            if current_time - cache_time < self.cache_duration:
                active_entries += 1
            else:
                expired_entries += 1
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "cache_duration_hours": self.cache_duration.total_seconds() / 3600
        }

# Global instance
tldr_service = TLDRService()
