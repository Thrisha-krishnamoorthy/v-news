from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import re

import os
os.environ["GOOGLE_API_KEY"] = "YOUR API KEY"

# Initialize Gemini model for all queries
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

# We're not using the pro model anymore since it's not available
# Just use the flash model for all queries
llm_advanced = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.4)

standard_prompt = PromptTemplate(
    input_variables=["news_text"],
    template="""
You are an AI trained to detect fake news.

Given the following aggregated news headlines and descriptions, analyze each one and respond with:
1. 🔍 A short summary of what it says.
2. ✅ A real-vs-fake probability score (0-100% real).
3. 🧠 A short explanation of why you gave that score.
4. 📊 A credibility score for the source (0-10).

News Articles:
{news_text}

Format your output like this:

### Title: [TITLE]
- 📰 Summary: ...
- 🧪 Real vs Fake Probability: 85%
- ℹ️ Explanation: ...
- 🏷️ Source Credibility: 8/10

Repeat for each article.
"""
)

advanced_prompt = PromptTemplate(
    input_variables=["news_text", "query"],
    template="""
You are an expert AI system trained to analyze news for authenticity, bias, and relevance to a search query.

SEARCH QUERY: {query}

Analyze these news articles for authenticity and relevance to the search query above:

{news_text}

For each article, provide:
1. 🔍 A comprehensive summary (2-3 sentences)
2. 🎯 Relevance score to the query (0-100%)
3. ✅ Real-vs-fake probability (0-100% real)
4. 🧠 Analysis of potential bias or misinformation (2-3 sentences)
5. 📊 Credibility rating for the source (0-10)
6. 🔑 Key facts or claims made in the article

Format your output exactly like this for each article:

### Title: [TITLE]
- 📰 Summary: ...
- 🎯 Relevance to Query: 85%
- 🧪 Real vs Fake Probability: 90%
- ℹ️ Analysis: ...
- 🏷️ Source Credibility: 8/10
- 🔑 Key Claims: 
  * Claim 1
  * Claim 2

Repeat for each article.
"""
)

news_checker_chain = LLMChain(llm=llm, prompt=standard_prompt)
advanced_news_checker_chain = LLMChain(llm=llm_advanced, prompt=advanced_prompt)

def analyze_news(news_list):
    """Analyze a list of news articles using the standard model"""
    # Safety check for empty list
    if not news_list:
        return "No news articles to analyze."
        
    combined = "\n\n".join([f"{n['title']} - {n['description']} ({n['source']})" for n in news_list])
    
    # If combined text is short enough for standard model
    if len(combined) < 10000:
        return news_checker_chain.run(news_text=combined)
    else:
        # If too long, truncate to first few articles
        truncated = "\n\n".join([f"{n['title']} - {n['description']} ({n['source']})" for n in news_list[:5]])
        return news_checker_chain.run(news_text=truncated)

def advanced_analyze_news(news_list, original_query):
    """Analyze news with the advanced analysis for more detailed analysis, particularly for longer queries"""
    # Safety check for empty list
    if not news_list:
        return "No news articles to analyze."
    
    # Limit number of articles to analyze to prevent context length issues
    limited_news = news_list[:8]  # Limit to 8 articles max for advanced analysis
        
    # Combine all news articles with their details
    combined = "\n\n".join([
        f"{n['title']} - {n['description']} (Source: {n['source']}, Published: {n.get('publishedAt', 'N/A')})" 
        for n in limited_news
    ])
    
    try:
        # For very long combined text, analyze even fewer articles
        if len(combined) > 15000:
            truncated = "\n\n".join([
                f"{n['title']} - {n['description']} (Source: {n['source']}, Published: {n.get('publishedAt', 'N/A')})" 
                for n in limited_news[:5]  # Further limit to 5 articles if too long
            ])
            return advanced_news_checker_chain.run(news_text=truncated, query=original_query)
        
        # For manageable length, analyze all articles (up to the 8 limit)
        return advanced_news_checker_chain.run(news_text=combined, query=original_query)
    except Exception as e:
        # If any error occurs, fall back to standard analysis
        print(f"Error in advanced analysis: {e}. Falling back to standard analysis.")
        return analyze_news(news_list)

def extract_probabilities(analysis_text):
    """Extract probability scores from the analysis text"""
    probabilities = []
    
    # Look for probability percentage patterns
    for match in re.finditer(r'Real vs Fake Probability:\s*(\d+)%', analysis_text):
        if match and match.group(1):
            try:
                probability = int(match.group(1))
                probabilities.append(probability)
            except ValueError:
                continue
    
    return probabilities if probabilities else [50]  # Default to 50% if none found
