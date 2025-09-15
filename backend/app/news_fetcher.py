import requests

def fetch_articles(api_key):
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data.get("status") != "ok":
        print("NewsAPI error:", data)
        return []

    articles = []
    for item in data.get("articles", [])[:5]:
        articles.append({
            "title": item.get("title", "No title"),
            "url": item.get("url", ""),
            "source": item.get("source", {}).get("name", ""),
            "content": item.get("content") or item.get("description", "")
        })
    return articles
