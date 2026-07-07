import streamlit as st
from news_feed import get_news_by_categories, get_related_news, search_long_form

def save_news(user_id, title, url, source, category="General"):
    """Save a news article for a user"""
    import sqlite3
    conn = sqlite3.connect("news_app.db")
    c = conn.cursor()
    c.execute('''
        INSERT INTO saved_news (user_id, title, url, source)
        VALUES (?, ?, ?, ?)
    ''', (user_id, title, url, source))
    conn.commit()
    conn.close()

def log_click(user_id, title, category):
    """Log user click on a news article for recommendations"""
    import sqlite3
    try:
        conn = sqlite3.connect("news_app.db")
        c = conn.cursor()
        
        # First check if the clicks table exists, create it if not
        c.execute('''
            CREATE TABLE IF NOT EXISTS clicks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                category TEXT,
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # Then log the click
        c.execute("INSERT INTO clicks (user_id, title, category) VALUES (?, ?, ?)",
                (user_id, title, category))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error logging click: {e}")
        return False

def render_news_detail(news_item, user_id):
    """Render a detailed view of a news article with related news"""
    # Store the liked category in session state if not present
    if "liked_categories" not in st.session_state:
        st.session_state.liked_categories = []
    
    # Main article content
    st.subheader(news_item.get("title", "No Title"))
    
    # Show source with badge-like styling (dark theme compatible)
    st.markdown(f"""
    <div style="background-color:rgba(70, 70, 70, 0.2);padding:5px 10px;border-radius:5px;display:inline-block;margin-bottom:15px;">
        <span style="color:#ffffff;font-size:14px;">📰 <a href="{news_item.get('url', '#')}" target="_blank" style="color:#ffffff;text-decoration:none;border-bottom:1px dotted #ffffff;">{news_item.get('source', 'Unknown')}</a> • {news_item.get('country', 'Unknown')}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Description in a card-like container with dark theme
    st.markdown(f"""
    <div style="background-color:rgba(30, 30, 30, 0.7);padding:15px;border-radius:5px;border:1px solid #444;margin-bottom:20px;color:#ffffff;">
        {news_item.get('description', 'No description available.')}
    </div>
    """, unsafe_allow_html=True)
    
    # Button to read full article
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"[🔗 Read Full Article]({news_item.get('url', '#')})")
    
    # Like button
    with col2:
        current_category = news_item.get("category", "general").lower()
        is_liked = current_category in st.session_state.liked_categories
        
        if st.button("❤️ Like" if not is_liked else "❤️ Liked", 
                    key=f"like_btn_{news_item.get('title', '')[:10]}",
                    type="primary" if is_liked else "secondary"):
            
            # Toggle like status
            if not is_liked:
                st.session_state.liked_categories.append(current_category)
                st.success(f"Added {current_category} to your interests!")
            else:
                st.session_state.liked_categories.remove(current_category)
                st.info(f"Removed {current_category} from your interests.")
            
            # Log the click for recommendations
            log_click(user_id, news_item.get("title", ""), current_category)
            st.rerun()
    
    # Save button
    with col3:
        if st.button("💾 Save article"):
            save_news(
                user_id,
                news_item.get("title", ""),
                news_item.get("url", ""),
                news_item.get("source", "Unknown"),
                news_item.get("category", "General")
            )
            st.success("✅ Article saved!")
    
    # Log the click quietly in the background
    log_click(user_id, news_item.get("title", ""), news_item.get("category", "general"))

    # Show Related News at the bottom
    st.markdown("---")
    st.subheader("🧩 Related News for Your Interests")
    
    # Get the current category
    current_category = news_item.get("category", "general").lower()
    
    # Get all liked categories - include current category if not already liked
    liked_categories = st.session_state.liked_categories.copy()
    if current_category not in liked_categories:
        liked_categories.append(current_category)
    
    # If still no categories, use general
    if not liked_categories:
        liked_categories = ["general"]
    
    # Create tabs for different related news categories
    if len(liked_categories) > 0:
        # First tab is for content related to current article
        tab_labels = ["Related To This Article"] + [category.capitalize() for category in liked_categories]
        tabs = st.tabs(tab_labels)
        
        # First tab: Content directly related to current article using keywords
        with tabs[0]:
            try:
                # Get title and description from current article
                title = news_item.get("title", "")
                description = news_item.get("description", "")
                
                # For articles with sufficient content, use long form search for better relevance
                if len(description) > 100:
                    # Combine title and description as a long search query
                    search_query = f"{title}. {description[:250]}"
                    related = search_long_form(search_query, max_results=4)
                    
                    # If long form search fails or returns nothing, fall back to keyword approach
                    if not related:
                        related = get_related_news(news_item)
                else:
                    # For shorter articles, use the regular related news function
                    related = get_related_news(news_item)
                
                if related:
                    # Display related news in a grid layout
                    for j in range(0, min(len(related), 4), 2):  # Show up to 4 articles
                        cols = st.columns(2)
                        
                        # First article in row
                        with cols[0]:
                            if j < len(related):
                                article = related[j]
                                st.markdown(f"""
                                <div style="background-color:rgba(30, 30, 30, 0.5);padding:10px;border-radius:5px;margin-bottom:10px;">
                                    <h4 style="color:#ffffff;">{article.get('title', 'No Title')}</h4>
                                    <p style="color:#aaaaaa;font-size:12px;">
                                        <a href='{article.get('url', '#')}' target='_blank' style="color:#aaaaaa;">{article.get('source', 'Unknown')}</a> • {article.get('country', 'Unknown')}
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                if st.button("Read", key=f"rel_semantic_{j}"):
                                    st.session_state.news_detail = article
                                    st.rerun()
                        
                        # Second article in row
                        with cols[1]:
                            if j+1 < len(related):
                                article = related[j+1]
                                st.markdown(f"""
                                <div style="background-color:rgba(30, 30, 30, 0.5);padding:10px;border-radius:5px;margin-bottom:10px;">
                                    <h4 style="color:#ffffff;">{article.get('title', 'No Title')}</h4>
                                    <p style="color:#aaaaaa;font-size:12px;">
                                        <a href='{article.get('url', '#')}' target='_blank' style="color:#aaaaaa;">{article.get('source', 'Unknown')}</a> • {article.get('country', 'Unknown')}
                                    </p>
                                </div>
                                """, unsafe_allow_html=True)
                                if st.button("Read", key=f"rel_semantic_{j+1}"):
                                    st.session_state.news_detail = article
                                    st.rerun()
                else:
                    st.info("No semantically related articles found. Try another article.")
            except Exception as e:
                st.error(f"Unable to load related news: {str(e)}")
                st.info("Try refreshing the page or selecting a different article.")
        
        # Additional tabs for liked categories
        for i, category in enumerate(liked_categories):
            with tabs[i+1]:  # +1 because the first tab is for semantic relations
                try:
                    # Get country from current article if available
                    country = news_item.get("country", "")
                    
                    # Map country names to codes if needed
                    country_mapping = {
                        "India": "in",
                        "USA": "us",
                        "UK": "gb", 
                        "United Kingdom": "gb",
                        "Canada": "ca",
                        "Singapore": "sg",
                        "Australia": "au"
                    }
                    
                    # Try to fetch category-specific news
                    related = get_news_by_categories([category], [country])
                    
                    # Filter out current article
                    current_title = news_item.get("title", "")
                    related = [r for r in related if r.get("title") != current_title]
                    
                    if related:
                        # Display related news in a grid layout
                        for j in range(0, min(len(related), 4), 2):  # Show up to 4 articles
                            cols = st.columns(2)
                            
                            # First article in row
                            with cols[0]:
                                if j < len(related):
                                    article = related[j]
                                    st.markdown(f"""
                                    <div style="background-color:rgba(30, 30, 30, 0.5);padding:10px;border-radius:5px;margin-bottom:10px;">
                                        <h4 style="color:#ffffff;">{article.get('title', 'No Title')}</h4>
                                        <p style="color:#aaaaaa;font-size:12px;">
                                            <a href='{article.get('url', '#')}' target='_blank' style="color:#aaaaaa;">{article.get('source', 'Unknown')}</a> • {article.get('country', 'Unknown')}
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    if st.button("Read", key=f"rel_{category}_{j}"):
                                        st.session_state.news_detail = article
                                        st.rerun()
                            
                            # Second article in row
                            with cols[1]:
                                if j+1 < len(related):
                                    article = related[j+1]
                                    st.markdown(f"""
                                    <div style="background-color:rgba(30, 30, 30, 0.5);padding:10px;border-radius:5px;margin-bottom:10px;">
                                        <h4 style="color:#ffffff;">{article.get('title', 'No Title')}</h4>
                                        <p style="color:#aaaaaa;font-size:12px;">
                                            <a href='{article.get('url', '#')}' target='_blank' style="color:#aaaaaa;">{article.get('source', 'Unknown')}</a> • {article.get('country', 'Unknown')}
                                        </p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    if st.button("Read", key=f"rel_{category}_{j+1}"):
                                        st.session_state.news_detail = article
                                        st.rerun()
                    else:
                        st.info(f"No related articles found for {category}. Try liking more articles.")
                except Exception as e:
                    st.error(f"Unable to load related news for {category}: {str(e)}")
                    st.info("Try refreshing the page or selecting a different article.")
    else:
        st.info("Like articles to see related content based on your interests!") 