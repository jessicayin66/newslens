from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.news_fetcher import fetch_articles, fetch_multiple_pages
from app.models import Article, BiasAnalysis, BalancedDietRequest
from app.bias_analyzer import BiasAnalyzer
from app.tldr_service import tldr_service
from pathlib import Path
from dotenv import load_dotenv
from app.ai_summary import summarize_article
import os
from datetime import datetime

env_path = Path(__file__).parent.parent / ".env" 
load_dotenv(dotenv_path=env_path)

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

app = FastAPI()

# Initialize bias analyzer
bias_analyzer = BiasAnalyzer()

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
    # Fetch articles (limited to 100 for free NewsAPI accounts)
    articles = fetch_multiple_pages(NEWS_API_KEY, category=category, total_articles=100)
    summarized_articles = []
    
    for a in articles:
        summary = summarize_article(a.get("content", ""), sentence_count=3)
        
        article_data = {
            "title": a.get("title", ""),
            "source": a.get("source", ""),
            "summary": summary,
            "url": a.get("url", "")
        }
        
        # Add bias analysis if requested
        if include_bias:
            try:
                bias_analysis = bias_analyzer.analyze_bias(
                    a.get("title", ""), 
                    a.get("content", "")
                )
                article_data["bias_analysis"] = bias_analysis
            except Exception as e:
                print(f"Error analyzing bias: {e}")
                article_data["bias_analysis"] = {
                    "bias_score": 0.0,
                    "bias_category": "neutral",
                    "confidence": 0.0,
                    "details": {"error": str(e)}
                }
        
        summarized_articles.append(article_data)
    
    return summarized_articles

@app.post("/articles/balanced")
async def get_balanced_articles(request: BalancedDietRequest):
    """Get a balanced mix of articles based on political bias."""
    articles = fetch_multiple_pages(NEWS_API_KEY, category=request.category, total_articles=100)
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

@app.get("/bias-stats")
async def get_bias_statistics(category: str = "all"):
    """Get bias statistics for articles in a category."""
    articles = fetch_multiple_pages(NEWS_API_KEY, category=category, total_articles=100)
    bias_stats = {"left-leaning": 0, "neutral": 0, "right-leaning": 0}
    
    for a in articles:  # Analyze all available articles for stats
        try:
            bias_analysis = bias_analyzer.analyze_bias(
                a.get("title", ""), 
                a.get("content", "")
            )
            category = bias_analysis.get("bias_category", "neutral")
            if category in bias_stats:
                bias_stats[category] += 1
        except Exception as e:
            bias_stats["neutral"] += 1
    
        return {
            "category": category,
            "bias_distribution": bias_stats,
            "total_analyzed": sum(bias_stats.values())
        }

@app.get("/tldr/{category}")
async def get_category_tldr(category: str = "all", force_refresh: bool = False):
    """Get TL;DR summary for a specific category."""
    try:
        result = tldr_service.get_category_tldr(category, force_refresh)
        return result
    except Exception as e:
        return {
            "category": category,
            "date": "Today",
            "total_clusters": 0,
            "total_articles": 0,
            "summaries": [],
            "error": str(e)
        }

@app.get("/tldr")
async def get_all_tldr(force_refresh: bool = False):
    """Get TL;DR summaries for all categories."""
    try:
        result = tldr_service.get_all_categories_tldr(force_refresh=force_refresh)
        return result
    except Exception as e:
        return {
            "date": "Today",
            "total_categories": 0,
            "total_articles": 0,
            "total_clusters": 0,
            "categories": {},
            "error": str(e)
        }

@app.get("/trending/{category}")
async def get_trending_topics(category: str = "all", min_cluster_size: int = 3):
    """Get trending topics for a category."""
    try:
        trending = tldr_service.get_trending_topics(category, min_cluster_size)
        return {
            "category": category,
            "trending_topics": trending,
            "count": len(trending)
        }
    except Exception as e:
        return {
            "category": category,
            "trending_topics": [],
            "count": 0,
            "error": str(e)
        }

@app.post("/tldr/clear-cache")
async def clear_tldr_cache():
    """Clear the TL;DR cache."""
    try:
        tldr_service.clear_cache()
        return {"message": "TL;DR cache cleared successfully"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/tldr/cache-stats")
async def get_tldr_cache_stats():
    """Get TL;DR cache statistics."""
    try:
        stats = tldr_service.get_cache_stats()
        return stats
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "news-analyzer-backend"
    }
