import requests

def fetch_articles(api_key, category=None, page_size=20, page=1):
    """
    Fetch top headlines from NewsAPI.
    - category: one of 'business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology'
    - page_size: number of articles per request (max 100)
    - page: which page of results to fetch
    """
    url = f"https://newsapi.org/v2/top-headlines"
    params = {
        "country": "us",
        "apiKey": api_key,
        "pageSize": page_size,
        "page": page
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
    return articles
