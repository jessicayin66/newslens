from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.news_fetcher import fetch_articles, fetch_multiple_pages
from app.models import Article, BiasAnalysis, BalancedDietRequest
from app.bias_analyzer import BiasAnalyzer
from pathlib import Path
from dotenv import load_dotenv
from app.ai_summary import summarize_article
import os

env_path = Path(__file__).parent.parent / ".env" 
load_dotenv(dotenv_path=env_path)

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

app = FastAPI()

# Initialize bias analyzer
bias_analyzer = BiasAnalyzer()

origins = [
    "http://localhost:5173",
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
