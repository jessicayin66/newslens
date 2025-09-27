import requests

def fetch_articles(api_key, category=None, page_size=100, page=1):
    """
    Fetch articles from NewsAPI (US and Canada news).
    - category: one of 'business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology'
    - page_size: number of articles per request (max 100)
    - page: which page of results to fetch
    """
    # Use 'top-headlines' endpoint with US and Canada
    url = f"https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": api_key,
        "pageSize": page_size,
        "page": page,
        "country": "us"  # Start with US
    }

    if category and category.lower() != "all":
        params["category"] = category.lower()

    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") != "ok":
        print("NewsAPI error:", data)
        return []

    articles = []
    for item in data.get("articles", []):
        articles.append({
            "title": item.get("title", "No title"),
            "url": item.get("url", ""),
            "source": item.get("source", {}).get("name", ""),
            "content": item.get("content") or item.get("description", "")
        })
    
    # Also fetch from Canada
    params["country"] = "ca"
    response_ca = requests.get(url, params=params)
    data_ca = response_ca.json()
    
    if data_ca.get("status") == "ok":
        for item in data_ca.get("articles", []):
            articles.append({
                "title": item.get("title", "No title"),
                "url": item.get("url", ""),
                "source": item.get("source", {}).get("name", ""),
                "content": item.get("content") or item.get("description", "")
            })
    
    return articles

def fetch_multiple_pages(api_key, category=None, total_articles=100):
    """
    Fetch articles from NewsAPI (US and Canada, limited to 100 for free accounts).
    - total_articles: number of articles to fetch (max 100 for free accounts)
    """
    # Fetch from both US and Canada (this might exceed 100, but we'll limit it)
    articles = fetch_articles(api_key, category=category, page_size=50, page=1)  # 50 from each country
    
    # Remove duplicates based on title and source
    seen_articles = set()
    unique_articles = []
    
    for article in articles:
        article_key = f"{article.get('title', '')}_{article.get('source', '')}"
        if article_key not in seen_articles and article.get('title'):
            seen_articles.add(article_key)
            unique_articles.append(article)
            # Limit to 100 articles total for free account
            if len(unique_articles) >= 100:
                break
    
    return unique_articles
