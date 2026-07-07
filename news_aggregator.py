# news_aggregator.py

import requests
import os

NEWS_API_KEY = "635d28530f843a0aa7afa2a0e22bd7c"  # Replace this with your actual API key

def get_latest_news(country="in", category=None, page_size=5):
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": NEWS_API_KEY,
        "country": country,
        "pageSize": page_size
    }
    if category:
        params["category"] = category

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return [{"title": "Error fetching news", "content": response.text, "source": "NewsAPI"}]

    data = response.json()
    news_list = []

    for article in data.get("articles", []):
        news_list.append({
            "title": article.get("title"),
            "content": article.get("description") or article.get("content"),
            "source": article.get("source", {}).get("name"),
            "url": article.get("url")
        })

    return news_list
