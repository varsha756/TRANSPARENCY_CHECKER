import os
import requests
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"


def get_ngo_news(
    query='"NGO" OR "nonprofit" OR "charity" OR "NGO funding" OR "nonprofit transparency"',
    page_size=8,
):
    """
    Fetch latest NGO-related news articles.
    Returns a list of dicts: title, source, url, published_at
    """
    if not NEWS_API_KEY:
        return []

    params = {
        "q": query,
        "qInTitle": query,       # require the keyword to appear in the title,
                                  # not just somewhere in the article body
        "language": "en",
        "sortBy": "relevancy",   # filter for relevance first...
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        articles = data.get("articles", [])

        results = [
            {
                "title": a["title"],
                "source": a["source"]["name"],
                "url": a["url"],
                "published_at": a["publishedAt"][:10],
            }
            for a in articles
            if a.get("title")
        ]

        # ...then sort the relevant results by recency
        results.sort(key=lambda x: x["published_at"], reverse=True)
        return results

    except requests.exceptions.RequestException:
        return []