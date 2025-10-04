from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.news_fetcher import fetch_articles, fetch_multiple_pages
from app.models import Article, BiasAnalysis, BalancedDietRequest
from app.tldr_service import tldr_service
from pathlib import Path
from dotenv import load_dotenv
from app.ai_summary import summarize_article
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env_path = Path(__file__).parent.parent / ".env" 
load_dotenv(dotenv_path=env_path)

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

app = FastAPI()

# Simple bias analyzer without heavy ML models
class SimpleBiasAnalyzer:
    def __init__(self):
        self.left_keywords = [
            'progressive', 'liberal', 'democrat', 'social justice', 'equality',
            'climate change', 'renewable energy', 'healthcare reform', 'minimum wage',
            'gun control', 'immigration reform', 'diversity', 'inclusion',
            'environmental protection', 'green energy', 'social welfare'
        ]
        
        self.right_keywords = [
            'conservative', 'republican', 'traditional values', 'free market',
            'small government', 'tax cuts', 'deregulation', 'law and order',
            'national security', 'border security', 'family values', 'religious freedom',
            'fiscal responsibility', 'entrepreneurship', 'individual liberty'
        ]
    
    def analyze_bias(self, title: str, content: str):
        """Simple keyword-based bias analysis."""
        text = f"{title} {content}".lower()
        
        left_count = sum(1 for keyword in self.left_keywords if keyword in text)
        right_count = sum(1 for keyword in self.right_keywords if keyword in text)
        
        total_keywords = left_count + right_count
        if total_keywords == 0:
            return {
                'bias_score': 0.0,
                'bias_category': 'neutral',
                'confidence': 0.0,
                'details': {'method': 'keyword-based', 'keywords_found': 0}
            }
        
        bias_score = (right_count - left_count) / total_keywords
        
        if bias_score < -0.2:
            category = 'left-leaning'
        elif bias_score > 0.2:
            category = 'right-leaning'
        else:
            category = 'neutral'
        
        return {
            'bias_score': bias_score,
            'bias_category': category,
            'confidence': min(1.0, total_keywords / 10.0),
            'details': {
                'method': 'keyword-based',
                'left_keywords': left_count,
                'right_keywords': right_count,
                'total_keywords': total_keywords
            }
        }
    
    def get_balanced_articles(self, articles, target_balance=None):
        """Simple balanced article selection."""
        if not target_balance:
            target_balance = {'left-leaning': 3, 'neutral': 4, 'right-leaning': 3}
        
        bias_groups = {'left-leaning': [], 'neutral': [], 'right-leaning': []}
        
        for article in articles:
            bias_category = article.get('bias_category', 'neutral')
            if bias_category in bias_groups:
                bias_groups[bias_category].append(article)
        
        balanced_articles = []
        for category, target_count in target_balance.items():
            available_articles = bias_groups.get(category, [])
            selected = available_articles[:target_count]
            balanced_articles.extend(selected)
        
        return balanced_articles

# Initialize simple bias analyzer
bias_analyzer = SimpleBiasAnalyzer()

origins = [
    "http://localhost:5173",
    "https://news-analyzer-frontend.onrender.com",
]

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/articles")
async def get_articles(category: str = "all", include_bias: bool = True):
    """Get articles with optional bias analysis."""
    try:
        # Fetch articles (limited to 50 for free tier)
        articles = fetch_multiple_pages(NEWS_API_KEY, category=category, total_articles=50)
        summarized_articles = []
        
        for a in articles:
            summary = summarize_article(a.get("content", ""), sentence_count=3)
            
            article_data = {
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "summary": summary,
                "url": a.get("url", "")
            }
            
            # Add simple bias analysis if requested
            if include_bias:
                try:
                    bias_analysis = bias_analyzer.analyze_bias(
                        a.get("title", ""), 
                        a.get("content", "")
                    )
                    article_data["bias_analysis"] = bias_analysis
                except Exception as e:
                    logger.error(f"Error analyzing bias: {e}")
                    article_data["bias_analysis"] = {
                        "bias_score": 0.0,
                        "bias_category": "neutral",
                        "confidence": 0.0,
                        "details": {"error": str(e)}
                    }
            
            summarized_articles.append(article_data)
        
        return summarized_articles
        
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        return {"error": str(e)}

@app.post("/articles/balanced")
async def get_balanced_articles(request: BalancedDietRequest):
    """Get a balanced mix of articles based on political bias."""
    try:
        articles = fetch_multiple_pages(NEWS_API_KEY, category=request.category, total_articles=50)
        analyzed_articles = []
        
        for a in articles:
            summary = summarize_article(a.get("content", ""), sentence_count=3)
            
            try:
                bias_analysis = bias_analyzer.analyze_bias(
                    a.get("title", ""), 
                    a.get("content", "")
                )
            except Exception as e:
                bias_analysis = {
                    "bias_score": 0.0,
                    "bias_category": "neutral",
                    "confidence": 0.0,
                    "details": {"error": str(e)}
                }
            
            article_data = {
                "title": a.get("title", ""),
                "source": a.get("source", ""),
                "summary": summary,
                "url": a.get("url", ""),
                "bias_analysis": bias_analysis
            }
            
            analyzed_articles.append(article_data)
        
        # Get balanced selection
        balanced_articles = bias_analyzer.get_balanced_articles(
            analyzed_articles, 
            request.target_balance
        )
        
        return {
            "articles": balanced_articles,
            "balance_info": {
                "total_analyzed": len(analyzed_articles),
                "selected": len(balanced_articles),
                "target_balance": request.target_balance
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting balanced articles: {e}")
        return {"error": str(e)}

@app.get("/bias-stats")
async def get_bias_statistics(category: str = "all"):
    """Get bias statistics for articles in a category."""
    try:
        articles = fetch_multiple_pages(NEWS_API_KEY, category=category, total_articles=50)
        bias_stats = {"left-leaning": 0, "neutral": 0, "right-leaning": 0}
        
        for a in articles:
            try:
                bias_analysis = bias_analyzer.analyze_bias(
                    a.get("title", ""), 
                    a.get("content", "")
                )
                category_name = bias_analysis.get("bias_category", "neutral")
                if category_name in bias_stats:
                    bias_stats[category_name] += 1
            except Exception as e:
                bias_stats["neutral"] += 1
        
        return {
            "category": category,
            "bias_distribution": bias_stats,
            "total_analyzed": sum(bias_stats.values())
        }
        
    except Exception as e:
        logger.error(f"Error getting bias stats: {e}")
        return {"error": str(e)}

@app.get("/tldr/{category}")
async def get_category_tldr(category: str = "all", force_refresh: bool = False):
    """Get TL;DR summary for a specific category (simplified version)."""
    try:
        # For lite version, return a simple summary without clustering
        articles = fetch_multiple_pages(NEWS_API_KEY, category=category, total_articles=20)
        
        if not articles:
            return {
                "category": category,
                "date": datetime.now().isoformat(),
                "total_clusters": 0,
                "total_articles": 0,
                "summaries": [],
                "note": "Lite version - no clustering"
            }
        
        # Create simple summaries
        summaries = []
        for i, article in enumerate(articles[:5]):  # Top 5 articles
            summary = summarize_article(article.get("content", ""), sentence_count=2)
            summaries.append({
                "title": article.get("title", ""),
                "summary": summary,
                "url": article.get("url", ""),
                "source": article.get("source", "")
            })
        
        return {
            "category": category,
            "date": datetime.now().isoformat(),
            "total_clusters": 1,
            "total_articles": len(articles),
            "summaries": summaries,
            "note": "Lite version - simplified clustering"
        }
        
    except Exception as e:
        logger.error(f"Error getting TL;DR: {e}")
        return {
            "category": category,
            "date": datetime.now().isoformat(),
            "total_clusters": 0,
            "total_articles": 0,
            "summaries": [],
            "error": str(e)
        }

@app.get("/tldr")
async def get_all_tldr(force_refresh: bool = False):
    """Get TL;DR summaries for all categories (simplified version)."""
    try:
        categories = ["business", "technology", "health", "sports", "entertainment"]
        result = {
            "date": datetime.now().isoformat(),
            "total_categories": len(categories),
            "total_articles": 0,
            "total_clusters": 0,
            "categories": {},
            "note": "Lite version - simplified processing"
        }
        
        for category in categories:
            category_result = await get_category_tldr(category, force_refresh)
            result["categories"][category] = category_result
            result["total_articles"] += category_result.get("total_articles", 0)
            result["total_clusters"] += category_result.get("total_clusters", 0)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting all TL;DR: {e}")
        return {
            "date": datetime.now().isoformat(),
            "total_categories": 0,
            "total_articles": 0,
            "total_clusters": 0,
            "categories": {},
            "error": str(e)
        }

@app.get("/trending/{category}")
async def get_trending_topics(category: str = "all", min_cluster_size: int = 3):
    """Get trending topics for a category (simplified version)."""
    try:
        articles = fetch_multiple_pages(NEWS_API_KEY, category=category, total_articles=30)
        
        # Simple keyword extraction for trending topics
        from collections import Counter
        import re
        
        all_words = []
        for article in articles:
            title = article.get("title", "").lower()
            words = re.findall(r'\b[a-zA-Z]{4,}\b', title)
            all_words.extend(words)
        
        # Filter out common words
        stop_words = {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'will', 'said', 'more', 'than', 'also', 'each', 'which', 'their', 'time', 'very', 'when', 'much', 'new', 'some', 'these', 'may', 'other', 'after', 'first', 'well', 'year', 'work', 'such', 'make', 'over', 'think', 'also', 'back', 'where', 'much', 'before', 'move', 'right', 'boy', 'old', 'too', 'same', 'she', 'all', 'there', 'when', 'up', 'use', 'word', 'how', 'said', 'an', 'each', 'which', 'do', 'their', 'time', 'if', 'will', 'about', 'out', 'many', 'then', 'them', 'can', 'only', 'other', 'new', 'some', 'what', 'time', 'very', 'when', 'much', 'get', 'through', 'back', 'much', 'before', 'go', 'good', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'}
        
        word_counts = Counter(all_words)
        trending = [word for word, count in word_counts.most_common(10) 
                   if word not in stop_words and count >= min_cluster_size]
        
        return {
            "category": category,
            "trending_topics": trending,
            "count": len(trending),
            "note": "Lite version - keyword-based trending"
        }
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        return {
            "category": category,
            "trending_topics": [],
            "count": 0,
            "error": str(e)
        }

@app.post("/tldr/clear-cache")
async def clear_tldr_cache():
    """Clear the TL;DR cache (no-op in lite version)."""
    return {"message": "Lite version - no cache to clear"}

@app.get("/tldr/cache-stats")
async def get_tldr_cache_stats():
    """Get TL;DR cache statistics (no-op in lite version)."""
    return {"message": "Lite version - no cache statistics"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "news-analyzer-backend-lite",
        "version": "lite"
    }
