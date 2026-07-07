import requests
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Keys
NEWS_API_KEY = "89fdac85a6b345c094fbf3b1582be178"  
NEWSDATA_API_KEY = "pub_31653e9e3a4e4c548c22f693ec7de45b72dfa"

def test_newsapi():
    """Test the NewsAPI directly"""
    try:
        logger.info("Testing NewsAPI...")
        url = f"https://newsapi.org/v2/top-headlines?country=us&category=technology&apiKey={NEWS_API_KEY}"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"NewsAPI error {response.status_code}: {data.get('message', 'Unknown error')}")
            return False
            
        if data.get("status") != "ok":
            logger.error(f"NewsAPI returned non-OK status: {data.get('status')} - {data.get('message', 'No message')}")
            return False
        
        articles = data.get("articles", [])
        logger.info(f"NewsAPI success: Got {len(articles)} articles")
        
        if articles:
            article = articles[0]
            logger.info(f"First article title: {article.get('title')}")
            logger.info(f"First article source: {article.get('source', {}).get('name')}")
        
        return True
    except Exception as e:
        logger.error(f"NewsAPI test failed with error: {str(e)}")
        return False

def test_newsdata():
    """Test the NewsData.io API directly"""
    try:
        logger.info("Testing NewsData.io API...")
        base_url = "https://newsdata.io/api/1/news"
        
        params = {
            "apikey": NEWSDATA_API_KEY,
            "language": "en",
            "category": "business"
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code != 200:
            logger.error(f"NewsData.io error {response.status_code}: {data.get('message', 'Unknown error')}")
            return False
            
        if data.get("status") != "success":
            logger.error(f"NewsData.io returned non-success status: {data.get('status')} - {data.get('message', 'No message')}")
            return False
        
        articles = data.get("results", [])
        logger.info(f"NewsData.io success: Got {len(articles)} articles")
        
        if articles:
            article = articles[0]
            logger.info(f"First article title: {article.get('title')}")
            logger.info(f"First article source: {article.get('source_id')}")
        
        return True
    except Exception as e:
        logger.error(f"NewsData.io test failed with error: {str(e)}")
        return False

def create_fallback_news():
    """Create some fallback news content"""
    return [
        {
            "title": "Global Tech Leaders Announce AI Collaboration",
            "description": "Major technology companies announced a collaborative initiative for ethical AI standards.",
            "url": "https://example.com/tech-ai-collaboration",
            "source": "Tech News",
            "category": "technology",
            "country": "World"
        },
        {
            "title": "Financial Markets Report Strong Performance",
            "description": "Global financial markets showed strong performance this quarter.",
            "url": "https://example.com/financial-markets",
            "source": "Finance Today",
            "category": "business",
            "country": "World"
        }
    ]

if __name__ == "__main__":
    logger.info("Starting direct API tests...")
    
    # Test NewsAPI
    news_api_success = test_newsapi()
    
    # Test NewsData.io
    newsdata_success = test_newsdata()
    
    # Summary
    if news_api_success and newsdata_success:
        logger.info("Both APIs are working correctly!")
    elif news_api_success:
        logger.info("Only NewsAPI is working correctly.")
    elif newsdata_success:
        logger.info("Only NewsData.io is working correctly.")
    else:
        logger.error("Both APIs failed!")
        logger.info("Using fallback news as a last resort:")
        fallback = create_fallback_news()
        for article in fallback:
            logger.info(f"Fallback article: {article['title']}")
    
    logger.info("Tests completed!") 