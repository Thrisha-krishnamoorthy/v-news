import news_feed
import logging
import json

# Set up logging to console for immediate feedback
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("test_news_feed")

def test_newsapi():
    """Test the NewsAPI functionality"""
    logger.info("Testing NewsAPI...")
    
    # Test query for global news
    url = f"https://newsapi.org/v2/everything?q=technology&pageSize=2&apiKey={news_feed.NEWS_API_KEY}"
    data = news_feed.fetch_from_newsapi(url)
    
    if data:
        logger.info("NewsAPI successful! Example article:")
        if data.get('articles'):
            article = data['articles'][0]
            logger.info(f"Title: {article.get('title')}")
            logger.info(f"Source: {article.get('source', {}).get('name')}")
        else:
            logger.warning("NewsAPI returned no articles")
    else:
        logger.error("NewsAPI test failed!")

def test_newsdata():
    """Test the NewsData.io API functionality"""
    logger.info("Testing NewsData.io...")
    
    base_url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": news_feed.NEWSDATA_API_KEY,
        "language": "en",
        "category": "business"
    }
    
    data = news_feed.fetch_from_newsdata(base_url, params)
    
    if data:
        logger.info("NewsData.io successful! Example article:")
        if data.get('results'):
            article = data['results'][0]
            logger.info(f"Title: {article.get('title')}")
            logger.info(f"Source: {article.get('source_id')}")
        else:
            logger.warning("NewsData.io returned no results")
    else:
        logger.error("NewsData.io test failed!")

def test_get_news_by_categories():
    """Test getting news by categories"""
    logger.info("Testing get_news_by_categories...")
    
    # Test with valid categories and countries
    categories = ["Technology", "Business"]
    countries = ["USA", "World"]
    
    articles = news_feed.get_news_by_categories(categories, countries)
    
    if articles:
        logger.info(f"Found {len(articles)} articles by category")
        logger.info("First article:")
        logger.info(f"Title: {articles[0].get('title')}")
        logger.info(f"Source: {articles[0].get('source')}")
        logger.info(f"Category: {articles[0].get('category')}")
        logger.info(f"Country: {articles[0].get('country')}")
    else:
        logger.warning("No articles found by category")

def test_get_news_feed():
    """Test getting a personalized news feed"""
    logger.info("Testing get_news_feed...")
    
    # Mock user interests
    interests = {
        "topics": ["Technology", "Sports"],
        "countries": ["USA", "India"]
    }
    
    articles = news_feed.get_news_feed(interests)
    
    if articles:
        logger.info(f"Found {len(articles)} articles for news feed")
        logger.info("First article:")
        logger.info(f"Title: {articles[0].get('title')}")
        logger.info(f"Source: {articles[0].get('source')}")
        logger.info(f"Category: {articles[0].get('category')}")
        logger.info(f"Country: {articles[0].get('country')}")
    else:
        logger.warning("No articles found for news feed")

def test_get_related_news():
    """Test getting related news"""
    logger.info("Testing get_related_news...")
    
    # Create a mock article
    mock_article = {
        "title": "Climate Change Impacts Global Agriculture",
        "description": "New studies show significant effects of climate change on crop yields worldwide, affecting food security in many regions.",
        "category": "science",
        "country": "World"
    }
    
    related = news_feed.get_related_news(mock_article, max_results=3)
    
    if related:
        logger.info(f"Found {len(related)} related articles")
        logger.info("First related article:")
        logger.info(f"Title: {related[0].get('title')}")
        logger.info(f"Source: {related[0].get('source')}")
    else:
        logger.warning("No related articles found")

def test_search_long_form():
    """Test searching with a long-form query"""
    logger.info("Testing search_long_form...")
    
    query = "What are the latest developments in renewable energy technology and how are they impacting global climate change efforts?"
    
    articles = news_feed.search_long_form(query, max_results=3)
    
    if articles:
        logger.info(f"Found {len(articles)} articles for search query")
        logger.info("First article:")
        logger.info(f"Title: {articles[0].get('title')}")
        logger.info(f"Source: {articles[0].get('source')}")
    else:
        logger.warning("No articles found for search query")

def test_fallback_news():
    """Test fallback news functionality"""
    logger.info("Testing fallback_news...")
    
    articles = news_feed.fallback_news()
    
    if articles:
        logger.info(f"Found {len(articles)} fallback articles")
        for article in articles:
            logger.info(f"Title: {article.get('title')}")
            logger.info(f"Category: {article.get('category')}")
    else:
        logger.error("No fallback articles available!")

if __name__ == "__main__":
    logger.info("Starting news feed tests...")
    
    # Test basic API connectivity
    test_newsapi()
    test_newsdata()
    
    # Test news fetching functions
    test_get_news_by_categories()
    test_get_news_feed()
    test_get_related_news()
    test_search_long_form()
    
    # Test fallback mechanism
    test_fallback_news()
    
    logger.info("All tests completed!") 