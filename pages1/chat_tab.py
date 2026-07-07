import streamlit as st
import requests
import google.generativeai as genai

# --- API Keys ---
SERPAPI_KEY = "50c5b82b39f2c0da7f5a43b261d8800ba05c466117583beb249b293f072db9ed"  # Replace with your key from https://serpapi.com/manage-api-key
GENAI_API_KEY = "AIzaSyD3ZGW08Dq2C7Ruq6TnosvbIyhhInOPXY8"  # From https://makersuite.google.com/app/apikey

# --- Configure Gemini ---
genai.configure(api_key=GENAI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")  # or "gemini-1.5-flash-latest"

# --- Fetch News from SerpAPI (Google News) ---
def fetch_news(query):
    params = {
        "q": query,
        "tbm": "nws",  # News search mode
        "api_key": SERPAPI_KEY,
        "num": 5,      # Number of results (max 100 for free tier)
        "hl": "en"      # Language (English)
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"SerpAPI error: {e}")
        return None

# --- Generate Answer from News ---
def generate_answer(query, news_results):
    if not news_results or "news_results" not in news_results:
        return "No relevant news found."

    # Prepare news context for Gemini
    news_context = "\n".join(
        f"Headline: {article['title']}\nSummary: {article.get('snippet', 'No summary')}\nSource: {article.get('source', 'Unknown')}\n"
        for article in news_results["news_results"]
    )

    prompt = f"""
    You are a news assistant. Answer the user's question strictly based on the news below.
    If the news is irrelevant, say: "No recent updates found."

    User Query: {query}
    Latest News:
    {news_context}
    """
    
    response = model.generate_content(prompt)
    return response.text

# --- Streamlit UI ---
def render():
    st.title("🔍 News Query Assistant Mr. V 🤖 ")
    user_query = st.text_input("Ask about any news event (e.g., 'why is stock market down?'):")

    if user_query:
        with st.spinner("Searching for news..."):
            news_data = fetch_news(user_query)
        
        if news_data:
            answer = generate_answer(user_query, news_data)
            st.write("**Answer:**", answer)
            
            # Optional: Show sources (hidden by default)
            with st.expander("View sources"):
                for article in news_data.get("news_results", []):
                    st.markdown(f"**{article['title']}**")
                    st.caption(f"*{article.get('snippet', 'No summary')}*")
                    st.write(f"Source: {article.get('source', 'Unknown')}")
                    st.divider()
        else:
            st.warning("No news found. Try a different query.")

if __name__ == "__main__":
    render()
