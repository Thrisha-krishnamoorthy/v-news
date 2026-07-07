import streamlit as st
import requests
import sqlite3
import time
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("news_feed")

# API Keys
NEWS_API_KEY = "89fdac85a6b345c094fbf3b1582be178"  
NEWSDATA_API_KEY = "pub_31653e9e3a4e4c548c22f693ec7de45b72dfa"

TOPIC_OPTIONS = [
    "business", "entertainment", "general", "health",
    "science", "sports", "technology", "politics", "finance", "stock"
]

COUNTRY_OPTIONS = {
    "India": "in",
    "USA": "us",
    "UK": "gb",
    "Canada": "ca",
    "Singapore": "sg",
    "Australia": "au",
    "World": "global"  # pseudo-country, we'll use everything
}

# NewsData.io country codes
NEWSDATA_COUNTRY_CODES = {
    "India": "in",
    "USA": "us",
    "UK": "gb",
    "Canada": "ca",
    "Singapore": "sg",
    "Australia": "au",
    "World": None  # No specific country for global news
}

# NewsData.io category mapping
NEWSDATA_CATEGORIES = {
    "business": "business",
    "entertainment": "entertainment",
    "general": "top",
    "health": "health",
    "science": "science",
    "sports": "sports",
    "technology": "technology",
    "politics": "politics",
    "finance": "business",
    "stock": "business"
}

# Map user-friendly topic names to API category names
TOPIC_TO_CATEGORY = {
    "Finance": "business",  
    "Sports": "sports",
    "Politics": "politics",
    "Stock": "business", 
    "Technology": "technology",
    "science": "science",
    "health": "health",
    "entertainment": "entertainment"
}

# Make all keys lowercase for case-insensitive matching
TOPIC_TO_CATEGORY = {k.lower(): v for k, v in TOPIC_TO_CATEGORY.items()}

# Function to fetch user interests from the database
def get_user_interests(user_id):
    try:
        conn = sqlite3.connect("news_app.db")
        c = conn.cursor()
        c.execute("SELECT topics, countries FROM user_interests WHERE user_id = ?", (user_id,))
        interests = c.fetchone()  # Only one row should exist for each user
        conn.close()

        if interests:
            topics = interests[0].split(",") if interests[0] else []
            countries = interests[1].split(",") if interests[1] else []
            return {"topics": topics, "countries": countries}
        return None
    except Exception as e:
        logger.error(f"Error getting user interests: {e}")
        return None

# Function to update user interests in the database
def update_user_interests(user_id, topics, countries):
    try:
        conn = sqlite3.connect("news_app.db")
        c = conn.cursor()
        
        # Convert lists to comma-separated strings
        topics_str = ",".join(topics) if topics else ""
        countries_str = ",".join(countries) if countries else ""
        
        # Check if user already has interests
        c.execute("SELECT id FROM user_interests WHERE user_id = ?", (user_id,))
        if c.fetchone():
            # Update existing
            c.execute("UPDATE user_interests SET topics = ?, countries = ? WHERE user_id = ?",
                     (topics_str, countries_str, user_id))
        else:
            # Insert new
            c.execute("INSERT INTO user_interests (user_id, topics, countries) VALUES (?, ?, ?)",
                     (user_id, topics_str, countries_str))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating user interests: {e}")
        return False

# Function to fetch news from NewsAPI with verbose error logging
def fetch_from_newsapi(url):
    logger.info(f"Fetching from NewsAPI: {url}")
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"NewsAPI error {response.status_code}: {data.get('message', 'Unknown error')}")
            return None
            
        if data.get("status") != "ok":
            logger.error(f"NewsAPI returned non-OK status: {data.get('status')} - {data.get('message', 'No message')}")
            return None
            
        logger.info(f"NewsAPI success: Got {len(data.get('articles', []))} articles")
        return data
    except requests.exceptions.Timeout:
        logger.error("NewsAPI request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"NewsAPI request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        logger.error("NewsAPI returned invalid JSON")
        return None
    except Exception as e:
        logger.error(f"Unexpected error with NewsAPI: {str(e)}")
        return None

# Function to fetch from NewsData.io with verbose error logging
def fetch_from_newsdata(base_url, params):
    logger.info(f"Fetching from NewsData.io: {base_url} with params {params}")
    try:
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"NewsData.io error {response.status_code}: {data.get('message', 'Unknown error')}")
            return None
            
        if data.get("status") != "success":
            logger.error(f"NewsData.io returned non-success status: {data.get('status')} - {data.get('message', 'No message')}")
            return None
            
        logger.info(f"NewsData.io success: Got {len(data.get('results', []))} articles")
        return data
    except requests.exceptions.Timeout:
        logger.error("NewsData.io request timed out")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"NewsData.io request failed: {str(e)}")
        return None
    except json.JSONDecodeError:
        logger.error("NewsData.io returned invalid JSON")
        return None
    except Exception as e:
        logger.error(f"Unexpected error with NewsData.io: {str(e)}")
        return None

# Function to get news by categories - UPDATED with better error handling
def get_news_by_categories(categories, countries=None):
    """Get news for specific categories and countries using both NewsAPI and NewsData.io"""
    logger.info(f"Getting news by categories: {categories} for countries: {countries}")
    
    if not categories:
        logger.warning("No categories provided to get_news_by_categories")
        return fallback_news()[:5]  # Return fallback news limited to 5 items
    
    # Default to USA if no countries specified
    if not countries:
        countries = ["USA"]
        logger.info("No countries specified, defaulting to USA")
    
    # Convert user-friendly topics to API categories
    api_categories = [TOPIC_TO_CATEGORY.get(cat.lower(), "general") for cat in categories]
    logger.info(f"Mapped categories to API categories: {api_categories}")
    
    all_articles = []
    api_success = False  # Track if any API call was successful
    
    # Get news for each country-category pair, prioritizing NewsAPI
    for country in countries:
        country_code = COUNTRY_OPTIONS.get(country, "us")
        logger.info(f"Processing country: {country} (NewsAPI code: {country_code})")
        
        for category in api_categories:
            logger.info(f"Processing category: {category}")
            
            # Try NewsAPI first with multiple query types
            try:
                # For "World" or "global", use everything endpoint directly
                if country_code == "global":
                    # Use the everything endpoint with the category as keyword
                    url = f"https://newsapi.org/v2/everything?q={category}&pageSize=3&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
                    data = fetch_from_newsapi(url)
                # For specific countries, try top-headlines first
                else:
                    # Try top headlines endpoint
                    url = f"https://newsapi.org/v2/top-headlines?country={country_code}&category={category}&pageSize=3&apiKey={NEWS_API_KEY}"
                    data = fetch_from_newsapi(url)
                    
                    # If no results, fall back to everything endpoint with country+category keywords
                    if not data or not data.get("articles"):
                        country_name = next((k for k, v in COUNTRY_OPTIONS.items() if v == country_code), country)
                        url = f"https://newsapi.org/v2/everything?q={category}+{country_name}&pageSize=3&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
                        data = fetch_from_newsapi(url)
                
                if data and data.get("status") == "ok":
                    api_success = True
                    for article in data.get("articles", []):
                        all_articles.append({
                            "title": article.get("title", "No Title"),
                            "description": article.get("description", ""),
                            "url": article.get("url", "#"),
                            "source": article.get("source", {}).get("name", "Unknown"),
                            "category": category,
                            "country": country
                        })
            except Exception as e:
                logger.error(f"Error fetching news from NewsAPI for {country}/{category}: {str(e)}")
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.5)
            
            # Only try NewsData.io if we didn't get enough articles from NewsAPI
            if len(all_articles) < 5:
                try:
                    newsdata_country_code = NEWSDATA_COUNTRY_CODES.get(country, None)
                    # Set up parameters for NewsData.io
                    base_url = "https://newsdata.io/api/1/news"
                    params = {
                        "apikey": NEWSDATA_API_KEY,
                        "language": "en"  # English language news
                    }
                    
                    # Add category if applicable
                    if category and category.lower() in NEWSDATA_CATEGORIES:
                        params["category"] = NEWSDATA_CATEGORIES[category.lower()]
                    
                    # Add country if applicable (not for "World")
                    if newsdata_country_code:
                        params["country"] = newsdata_country_code
                    
                    data = fetch_from_newsdata(base_url, params)
                    
                    if data and data.get("status") == "success" and "results" in data:
                        api_success = True
                        for article in data["results"][:2]:  # Limit to 2 articles per category-country pair
                            all_articles.append({
                                "title": article.get("title", "No Title"),
                                "description": article.get("description", ""),
                                "url": article.get("link", "#"),
                                "source": article.get("source_id", "Unknown"),
                                "category": category,
                                "country": country
                            })
                except Exception as e:
                    logger.error(f"Error fetching news from NewsData.io for {country}/{category}: {str(e)}")
    
    logger.info(f"Total articles collected before deduplication: {len(all_articles)}")
    
    # Remove duplicates based on title
    unique_articles = []
    titles = set()
    for article in all_articles:
        if article["title"] not in titles:
            titles.add(article["title"])
            unique_articles.append(article)
    
    logger.info(f"Final unique articles: {len(unique_articles)}")
    
    # If we still have no articles or no API calls succeeded, use fallback news
    if not unique_articles or not api_success:
        logger.warning("No articles found or all API calls failed, using fallback news")
        return fallback_news()[:5]  # Limit to 5 articles
    
    return unique_articles[:5]  # Return up to 5 articles

def get_related_news(article, max_results=4):
    """Get news related to a specific article based on keywords in its title and description
    using both NewsAPI and NewsData.io"""
    logger.info(f"Getting related news for article with title: {article.get('title', 'Unknown')}")
    
    if not article:
        logger.warning("No article provided to get_related_news")
        return fallback_news()[:max_results]
    
    # Extract keywords from article title and description
    title = article.get("title", "")
    description = article.get("description", "")
    
    # Remove common words and extract meaningful keywords
    import re
    from collections import Counter
    
    # Combine title and description
    text = f"{title} {description}"
    
    # Clean text - lowercase, remove punctuation, and split into words
    words = re.sub(r'[^\w\s]', '', text.lower()).split()
    
    # Common English stopwords to filter out
    stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                'is', 'are', 'was', 'were', 'be', 'been', 'being', 'by', 'with', 
                'about', 'against', 'between', 'into', 'through', 'during', 'before', 
                'after', 'above', 'below', 'from', 'up', 'down', 'of', 'off', 'over', 
                'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 
                'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 
                'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 
                'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 
                'now', 'this', 'that', 'these', 'those', 'what', 'which', 'who', 'whom'}
    
    # Filter out stopwords and short words
    filtered_words = [word for word in words if word not in stopwords and len(word) > 3]
    
    # Count word frequency
    word_counts = Counter(filtered_words)
    
    # Get the most common words as keywords (up to 5)
    keywords = [word for word, count in word_counts.most_common(5)]
    logger.info(f"Extracted keywords: {keywords}")
    
    if not keywords:
        # Fallback to category if no significant keywords found
        logger.warning("No keywords found, falling back to category-based news")
        return get_news_by_categories([article.get("category", "general")])
    
    # Build search query with the keywords
    search_query = " OR ".join(keywords)
    
    # Get country from article
    country = article.get("country", "World")
    country_code = COUNTRY_OPTIONS.get(country, "global")
    newsdata_country_code = NEWSDATA_COUNTRY_CODES.get(country, None)
    
    related_articles = []
    current_title = article.get("title", "")
    api_success = False
    
    # Fetch related news using keywords from NewsAPI
    try:
        # Use 'everything' endpoint for keyword search
        url = f"https://newsapi.org/v2/everything?q={search_query}&pageSize={max_results+1}&apiKey={NEWS_API_KEY}"
        data = fetch_from_newsapi(url)
        
        if data and data.get("status") == "ok":
            api_success = True
            for related in data.get("articles", []):
                # Skip the current article
                if related.get("title") == current_title:
                    continue
                    
                related_articles.append({
                    "title": related.get("title", "No Title"),
                    "description": related.get("description", ""),
                    "url": related.get("url", "#"),
                    "source": related.get("source", {}).get("name", "Unknown"),
                    "category": article.get("category", "general"),
                    "country": country
                })
                
                # Stop once we have enough articles
                if len(related_articles) >= max_results:
                    break
    except Exception as e:
        logger.error(f"Error fetching related news from NewsAPI: {str(e)}")
    
    # Add a small delay to avoid hitting rate limits
    time.sleep(0.5)
    
    # Now try with NewsData.io if we don't have enough articles
    if len(related_articles) < max_results:
        try:
            # Set up NewsData.io API query
            base_url = "https://newsdata.io/api/1/news"
            params = {
                "apikey": NEWSDATA_API_KEY,
                "language": "en",
                "q": search_query
            }
            
            # Add country if applicable (not for "World")
            if newsdata_country_code:
                params["country"] = newsdata_country_code
                
            # Make the API request
            data = fetch_from_newsdata(base_url, params)
            
            if data and data.get("status") == "success" and "results" in data:
                api_success = True
                for related in data["results"]:
                    # Skip if title matches current article
                    if related.get("title") == current_title:
                        continue
                    
                    related_articles.append({
                        "title": related.get("title", "No Title"),
                        "description": related.get("description", ""),
                        "url": related.get("link", "#"),
                        "source": related.get("source_id", "Unknown"),
                        "category": article.get("category", "general"),
                        "country": country
                    })
                    
                    # Stop once we have enough articles
                    if len(related_articles) >= max_results:
                        break
        except Exception as e:
            logger.error(f"Error fetching related news from NewsData.io: {str(e)}")
    
    # If we still don't have enough articles or no API call succeeded, try category-based news
    if len(related_articles) < max_results or not api_success:
        try:
            additional = get_news_by_categories([article.get("category", "general")], [country])
            
            # Add additional articles without duplicating titles
            existing_titles = {a["title"] for a in related_articles}
            for add_article in additional:
                if add_article["title"] not in existing_titles and add_article["title"] != current_title:
                    related_articles.append(add_article)
                    existing_titles.add(add_article["title"])
                    
                    if len(related_articles) >= max_results:
                        break
        except Exception as e:
            logger.error(f"Error getting additional category-based news: {str(e)}")
    
    # If we still have no articles after all attempts, use fallback
    if not related_articles:
        logger.warning("No related articles found after all attempts, using fallback news")
        # Filter fallback news to match the article's category if possible
        article_category = article.get("category", "").lower()
        filtered_fallback = [n for n in fallback_news() if n["category"].lower() == article_category]
        
        # If we have relevant fallback articles, use those; otherwise use general fallback
        if filtered_fallback:
            return filtered_fallback[:max_results]
        else:
            return fallback_news()[:max_results]
    
    logger.info(f"Found {len(related_articles)} related articles")
    return related_articles[:max_results]

def search_long_form(query, max_results=5):
    """
    Search for news using a longer, more complex query and return relevant articles
    from both NewsAPI and NewsData.io
    
    This function is optimized for handling longer search queries like questions,
    statements, or detailed topic descriptions.
    
    Args:
        query: The long search query (can be a question, statement, or detailed description)
        max_results: Maximum number of results to return
    
    Returns:
        List of relevant news articles
    """
    logger.info(f"Searching for news with query: {query}")
    
    if not query or len(query.strip()) < 5:
        logger.warning("Query too short or empty, returning fallback news")
        return fallback_news()[:max_results]
    
    # Process the long query to extract meaningful search terms
    import re
    from collections import Counter
    
    # Clean and normalize the query
    query = query.strip()
    
    # For very long queries, extract key terms
    if len(query) > 80:
        # Split into sentences
        sentences = re.split(r'[.!?]', query)
        
        # Extract meaningful words (simple approach - could be improved with NLP)
        important_words = []
        for sentence in sentences:
            # Remove common words
            words = re.sub(r'[^\w\s]', '', sentence.lower()).split()
            
            # Filter out common stop words and short words
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'by', 'with', 
                        'about', 'what', 'when', 'where', 'how', 'why', 'who', 'which', 'this', 
                        'that', 'these', 'those', 'they', 'them', 'their', 'have', 'has', 'had',
                        'not', 'don', 'all', 'any', 'very', 'will', 'should', 'can', 'could'}
            
            filtered_words = [word for word in words if word not in stopwords and len(word) > 3]
            important_words.extend(filtered_words)
        
        # Count word frequency
        word_counts = Counter(important_words)
        
        # Get most common words as search terms (up to 8)
        search_terms = [word for word, count in word_counts.most_common(8)]
        
        # Build search query using key terms with OR logic for broader results
        if len(search_terms) > 1:
            processed_query = " OR ".join(search_terms)
        else:
            # If insufficient terms extracted, use original but truncated
            processed_query = query[:150]
    else:
        # For shorter queries, use as-is
        processed_query = query
    
    logger.info(f"Processed query: {processed_query}")
    
    result_articles = []
    api_success = False
    
    # Attempt to fetch news from NewsAPI using the processed query
    try:
        # Use 'everything' endpoint for better semantic matching
        url = f"https://newsapi.org/v2/everything?q={processed_query}&language=en&pageSize={max_results+3}&sortBy=relevancy&apiKey={NEWS_API_KEY}"
        data = fetch_from_newsapi(url)
        
        if data and data.get("status") == "ok":
            api_success = True
            for article in data.get("articles", []):
                if article.get("title") and article.get("description"):
                    # Extract the primary category if possible
                    content = f"{article.get('title', '')} {article.get('description', '')}"
                    
                    # Simple keyword-based category extraction (could be improved with ML)
                    category = "general"
                    category_keywords = {
                        "business": ["business", "economy", "market", "stock", "finance", "trade", "economic"],
                        "technology": ["tech", "technology", "digital", "software", "hardware", "ai", "computing"],
                        "health": ["health", "medical", "medicine", "disease", "treatment", "doctor", "patient"],
                        "science": ["science", "scientific", "research", "study", "discovery"],
                        "sports": ["sport", "sports", "team", "player", "game", "match", "tournament"],
                        "politics": ["politics", "political", "government", "election", "policy", "minister", "president"],
                        "entertainment": ["entertainment", "movie", "film", "music", "celebrity", "actor", "actress"]
                    }
                    
                    content_lower = content.lower()
                    for cat, keywords in category_keywords.items():
                        if any(keyword in content_lower for keyword in keywords):
                            category = cat
                            break
                    
                    # Determine country from source or default to global
                    source_name = article.get("source", {}).get("name", "").lower()
                    country = "World"  # Default
                    
                    # Simple country detection based on domain or source name
                    country_indicators = {
                        "india": ["india", ".in", "indian", "times of india", "hindustan"],
                        "USA": ["usa", "us", "america", "american", ".com", "washington", "york"],
                        "UK": ["uk", "united kingdom", "british", ".co.uk", "bbc", "guardian"],
                        "Canada": ["canada", "canadian", ".ca"],
                        "Australia": ["australia", "australian", ".au"],
                        "Singapore": ["singapore", "singaporean", ".sg"]
                    }
                    
                    for c, indicators in country_indicators.items():
                        if any(ind in source_name for ind in indicators):
                            country = c
                            break
                    
                    result_articles.append({
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "url": article.get("url", "#"),
                        "source": article.get("source", {}).get("name", "Unknown"),
                        "publishedAt": article.get("publishedAt", ""),
                        "category": category,
                        "country": country
                    })
    except Exception as e:
        logger.error(f"Error in search_long_form with NewsAPI: {str(e)}")
    
    # Add a small delay to avoid hitting rate limits
    time.sleep(0.5)
        
    # Now try with NewsData.io API
    try:
        # Set up NewsData.io API query
        base_url = "https://newsdata.io/api/1/news"
        params = {
            "apikey": NEWSDATA_API_KEY,
            "language": "en",
            "q": processed_query
        }
            
        # Make the API request
        data = fetch_from_newsdata(base_url, params)
        
        if data and data.get("status") == "success" and "results" in data:
            api_success = True
            for article in data["results"]:
                # Extract category using the same keyword detection
                content = f"{article.get('title', '')} {article.get('description', '')}"
                category = "general"
                category_keywords = {
                    "business": ["business", "economy", "market", "stock", "finance", "trade", "economic"],
                    "technology": ["tech", "technology", "digital", "software", "hardware", "ai", "computing"],
                    "health": ["health", "medical", "medicine", "disease", "treatment", "doctor", "patient"],
                    "science": ["science", "scientific", "research", "study", "discovery"],
                    "sports": ["sport", "sports", "team", "player", "game", "match", "tournament"],
                    "politics": ["politics", "political", "government", "election", "policy", "minister", "president"],
                    "entertainment": ["entertainment", "movie", "film", "music", "celebrity", "actor", "actress"]
                }
                
                content_lower = content.lower() if content else ""
                for cat, keywords in category_keywords.items():
                    if any(keyword in content_lower for keyword in keywords):
                        category = cat
                        break
            
                # Determine country
                country = "World"  # Default
                if article.get("country"):
                    # Convert country codes back to names
                    for country_name, code in NEWSDATA_COUNTRY_CODES.items():
                        if code and code.lower() == article.get("country", "").lower():
                            country = country_name
                            break
                
                result_articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("link", "#"),
                    "source": article.get("source_id", "Unknown"),
                    "publishedAt": article.get("pubDate", ""),
                    "category": category,
                    "country": country
                })
    except Exception as e:
        logger.error(f"Error in search_long_form with NewsData.io: {str(e)}")
    
    # Remove duplicates
    unique_articles = []
    seen_titles = set()
    
    for article in result_articles:
        if article["title"] and article["title"] not in seen_titles:
            seen_titles.add(article["title"])
            unique_articles.append(article)
            if len(unique_articles) >= max_results:
                break
    
    # If no articles found from any API or no successful API calls, use fallback news
    if not unique_articles or not api_success:
        logger.warning("No articles found in search or all API calls failed, using fallback news")
        return fallback_news()[:max_results]
    
    logger.info(f"Found {len(unique_articles)} articles for search query")
    return unique_articles

# Function to fetch news from both APIs with more robust error handling
def get_news_feed(interests):
    """Get news based on user interests using both NewsAPI and NewsData.io"""
    logger.info(f"Getting news feed for interests: {interests}")
    
    if not interests or not interests.get("topics"):
        logger.warning("No interests or topics provided to get_news_feed")
        return fallback_news()
    
    topics = interests.get("topics", ["general"])
    countries = interests.get("countries", ["World"])
    
    logger.info(f"Topics: {topics}, Countries: {countries}")
    
    # Convert user-friendly topics to API categories
    api_categories = [TOPIC_TO_CATEGORY.get(topic.lower(), "general") for topic in topics]
    
    all_articles = []
    api_success = False  # Track if any API call was successful
    
    # Get news for each country-category pair, prioritizing NewsAPI
    for country in countries:
        country_code = COUNTRY_OPTIONS.get(country, "us")
        
        logger.info(f"Processing {country} with code: NewsAPI={country_code}")
        
        for category in api_categories:
            # Try NewsAPI first, using multiple endpoints for better coverage
            try:
                # Try top headlines first
                if country_code != "global":
                    url = f"https://newsapi.org/v2/top-headlines?country={country_code}&category={category}&pageSize=5&apiKey={NEWS_API_KEY}"
                    data = fetch_from_newsapi(url)
                    
                    if data and data.get("status") == "ok" and data.get("articles"):
                        api_success = True
                        for article in data.get("articles", []):
                            all_articles.append({
                                "title": article.get("title", "No Title"),
                                "description": article.get("description", ""),
                                "url": article.get("url", "#"),
                                "source": article.get("source", {}).get("name", "Unknown"),
                                "category": category,
                                "country": country
                            })
                
                # If we didn't get enough articles, try the everything endpoint
                if not api_success or len(all_articles) < 3:
                    # Everything endpoint with the category as the search term
                    url = f"https://newsapi.org/v2/everything?q={category}&pageSize=5&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
                    data = fetch_from_newsapi(url)
                    
                    if data and data.get("status") == "ok":
                        api_success = True
                        for article in data.get("articles", []):
                            all_articles.append({
                                "title": article.get("title", "No Title"),
                                "description": article.get("description", ""),
                                "url": article.get("url", "#"),
                                "source": article.get("source", {}).get("name", "Unknown"),
                                "category": category,
                                "country": country
                            })
            except Exception as e:
                logger.error(f"Error fetching news from NewsAPI for {country}/{category}: {str(e)}")
            
            # Add a small delay to avoid hitting rate limits
            time.sleep(0.5)
            
            # Try NewsData.io if NewsAPI didn't return enough articles, but with lower priority
            if not api_success or len(all_articles) < 5:
                try:
                    newsdata_country_code = NEWSDATA_COUNTRY_CODES.get(country, None)
                    # Set up NewsData.io API query
                    base_url = "https://newsdata.io/api/1/news"
                    params = {
                        "apikey": NEWSDATA_API_KEY,
                        "language": "en"
                    }
                    
                    # Add category if applicable
                    if category and category.lower() in NEWSDATA_CATEGORIES:
                        params["category"] = NEWSDATA_CATEGORIES[category.lower()]
                    
                    # Add country if applicable (not for "World")
                    if newsdata_country_code:
                        params["country"] = newsdata_country_code
                    
                    data = fetch_from_newsdata(base_url, params)
                    if data and data.get("status") == "success" and "results" in data:
                        api_success = True
                        for article in data["results"][:3]:
                            all_articles.append({
                                "title": article.get("title", "No Title"),
                                "description": article.get("description", ""),
                                "url": article.get("link", "#"),
                                "source": article.get("source_id", "Unknown"),
                                "category": category,
                                "country": country
                            })
                except Exception as e:
                    logger.error(f"Error fetching news from NewsData.io for {country}/{category}: {str(e)}")
    
    logger.info(f"Total articles collected before deduplication: {len(all_articles)}")
    
    # Remove duplicates
    unique_articles = []
    titles = set()
    for article in all_articles:
        if article["title"] not in titles:
            titles.add(article["title"])
            unique_articles.append(article)
    
    logger.info(f"Final unique articles: {len(unique_articles)}")
    
    # If no articles were found or no API calls succeeded, provide fallback content
    if not unique_articles or not api_success:
        logger.warning("No articles found from APIs or all API calls failed, using fallback news")
        return fallback_news()
    
    return unique_articles[:15]  # Return up to 15 articles

def fallback_news():
    """
    Provides hand-crafted fallback news in case both APIs fail
    """
    logger.warning("Using fallback news content - APIs must be down")
    return [
        {
            "title": "Global Tech Leaders Announce AI Collaboration",
            "description": "Major technology companies have announced a collaborative initiative to develop ethical AI standards and promote responsible innovation in artificial intelligence.",
            "url": "https://example.com/tech-ai-collaboration",
            "source": "Tech News",
            "category": "technology",
            "country": "World"
        },
        {
            "title": "Financial Markets Report Strong Performance",
            "description": "Global financial markets showed strong performance this quarter, with major indices reaching new highs despite ongoing economic challenges.",
            "url": "https://example.com/financial-markets",
            "source": "Finance Today",
            "category": "business",
            "country": "World"
        },
        {
            "title": "Sports Championship Series Breaks Viewing Records",
            "description": "This year's international sports championship has broken all previous viewing records, with billions of viewers tuning in worldwide.",
            "url": "https://example.com/sports-championship",
            "source": "Sports Network",
            "category": "sports",
            "country": "World"
        },
        {
            "title": "Healthcare Innovation: New Treatment Shows Promise",
            "description": "Researchers have announced promising results from clinical trials of a new treatment approach that could revolutionize care for patients.",
            "url": "https://example.com/healthcare-innovation",
            "source": "Health Journal",
            "category": "health",
            "country": "World"
        },
        {
            "title": "Climate Initiative Gains International Support",
            "description": "A new climate initiative has gained the support of over 100 countries, targeting significant reductions in carbon emissions by 2030.",
            "url": "https://example.com/climate-initiative",
            "source": "World News",
            "category": "science",
            "country": "World"
        }
    ]

# Main Streamlit app interface
def main():
    st.title("News Feed App")

    # Assume the user is logged in, and we know the user_id (this can be dynamic based on session)
    user_id = 1  # This would be dynamic in a real app

    # Fetch the user's current interests
    interests = get_user_interests(user_id)

    # Display news feed based on interests
    get_news_feed(interests)

    # Section to edit interests (hidden by default)
    with st.expander("Edit Your Interests"):
        # Let users change topics and countries
        new_topics = st.multiselect("Select topics of interest", TOPIC_OPTIONS, interests["topics"])
        new_countries = st.multiselect("Select countries of interest", list(COUNTRY_OPTIONS.keys()), interests["countries"])

        if st.button("Save Interests"):
            # Save new interests to the database
            update_user_interests(user_id, new_topics, new_countries)
            st.success("Your interests have been updated!")

if __name__ == "__main__":
    main()
