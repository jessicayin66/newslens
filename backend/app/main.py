from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.news_fetcher import fetch_articles
from app.models import Article
from pathlib import Path
from dotenv import load_dotenv
from app.ai_summary import summarize_article
import os

env_path = Path(__file__).parent.parent / ".env" 
load_dotenv(dotenv_path=env_path)

NEWS_API_KEY = os.getenv("NEWSAPI_KEY")

app = FastAPI()

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
async def get_articles():
    articles = fetch_articles(NEWS_API_KEY)
    summarized_articles = []
    
    for a in articles:
        summary = summarize_article(a.get("content", ""), sentence_count=3)
        summarized_articles.append({
            "title": a.get("title", ""),
            "source": a.get("source", ""),
            "summary": summary,
            "url": a.get("url", "")
        })
    
    return summarized_articles
