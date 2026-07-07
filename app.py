import streamlit as st
import sqlite3
from database import init_db
from auth_sqlite import create_user, authenticate_user, save_user_interests, get_user_interests
from news_feed import get_news_feed, update_user_interests, get_news_by_categories
from pages1 import aggregator_tab, chat_tab
from news_detail import render_news_detail, log_click

# Must be at the top before anything else
st.set_page_config(page_title=" 🤖 News  ", layout="wide")

TOPICS = ["Finance", "Sports", "Politics", "Stock", "Technology"]
COUNTRIES = ["World", "India", "USA", "Canada", "Singapore", "UK"]


init_db()

if "user" not in st.session_state:
    st.title("Login/Register")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = authenticate_user(username, password)
            if user:
                st.session_state.user = user
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        r_username = st.text_input("New Username")
        r_email = st.text_input("Email")
        r_password = st.text_input("New Password", type="password")
        if st.button("Register"):
            try:
                create_user(r_username, r_email, r_password)
                st.success("User registered! Go to Login.")
            except Exception as e:
                st.error("Username or Email already exists.")
else:
    st.sidebar.success(f"Welcome, {st.session_state.user['username']} 👋")

    # Sidebar navigation
    tab = st.sidebar.radio("📌 Navigation", ["📰 News Aggregator", "💬 Ask 🤖", "🗞️ News Feed"])

    if tab == "📰 News Aggregator":
        aggregator_tab.render()

    elif tab == "💬 Ask 🤖":
        print("fetch_grounded_context")
        chat_tab.render()

    elif tab == "🗞️ News Feed":
        st.title("🗞️ Your Personalized News Feed")
        
        # Manual collection of user interests
        with st.expander("✏️ Edit Your Interests", expanded=not get_user_interests(st.session_state.user["id"])):
            st.subheader("Select Your News Preferences")
            
            # Get existing interests or initialize empty
            interests = get_user_interests(st.session_state.user["id"]) or {"topics": [], "countries": []}
            
            # Let users select their interests
            new_topics = st.multiselect("📊 Topics You're Interested In:", 
                                       TOPICS, 
                                       default=interests.get("topics", []))
            
            new_countries = st.multiselect("🌎 Countries/Regions You Want News From:", 
                                          COUNTRIES, 
                                          default=interests.get("countries", []))
            
            if st.button("💾 Save My Preferences"):
                update_user_interests(st.session_state.user["id"], new_topics, new_countries)
                st.success("✅ Your preferences have been updated!")
                # Force a rerun to refresh the page with new preferences
                st.rerun()
        
        # Get the user's interests after potential update
        interests = get_user_interests(st.session_state.user["id"])
        
        if not interests or not (interests.get("topics") and interests.get("countries")):
            st.warning("⚠️ Please set your news preferences to see personalized content")
        else:
            # Initialize liked categories if not in session state
            if "liked_categories" not in st.session_state:
                st.session_state.liked_categories = []
                
            # 1. SUGGESTED NEWS SECTION (4-5 articles based on interests)
            st.header("🔍 Suggested For You")
            suggested_news = get_news_by_categories(
                interests.get("topics", [])[:2], 
                interests.get("countries", [])
            )[:5]  # Limit to top 5
            
            # Display suggested news in a prominent way
            if suggested_news:
                cols = st.columns(min(len(suggested_news), 3))  # Up to 3 columns
                for i, news in enumerate(suggested_news[:3]):  # First row - up to 3 articles
                    with cols[i % 3]:
                        st.markdown(f"**{news['title']}**")
                        st.markdown(f"*Source: <a href='{news.get('url', '#')}' target='_blank'>{news['source']}</a> ({news.get('country', 'Unknown')})*", unsafe_allow_html=True)
                        if st.button("Read More", key=f"sugg_{i}"):
                            st.session_state.news_detail = news
                            st.rerun()
                
                # Second row (if needed)
                if len(suggested_news) > 3:
                    for i, news in enumerate(suggested_news[3:5]):  # Only show up to 2 more
                        st.markdown(f"📌 **{news['title']}** - *<a href='{news.get('url', '#')}' target='_blank'>{news['source']}</a> ({news.get('country', 'Unknown')})*", unsafe_allow_html=True)
                        if st.button("Read More", key=f"sugg2_{i}"):
                            st.session_state.news_detail = news
                            st.rerun()
            else:
                st.info("No suggested news found for your preferences. Try selecting different topics or countries.")
            
            st.markdown("---")
            
            # 2. TOP NEWS SECTION (below suggestions)
            st.header("📰 Latest Top News")
            feed = get_news_feed(interests)
            
            if feed:
                for index, news_item in enumerate(feed):
                    with st.container():
                        # News card with columns for content and actions
                        cols = st.columns([3, 1])
                        
                        # News content column
                        with cols[0]:
                            st.markdown(f"### {news_item['title']}")
                            # Make source name clickable with link to original article
                            st.markdown(f"*Source: <a href='{news_item.get('url', '#')}' target='_blank'>{news_item['source']}</a> ({news_item.get('country', 'Unknown')})*", unsafe_allow_html=True)
                            
                            # Show description if available
                            if news_item.get('description'):
                                st.markdown(f"{news_item.get('description', '')[:150]}..." if len(news_item.get('description', '')) > 150 else news_item.get('description', ''))
                        
                        # Action buttons column
                        with cols[1]:
                            # Action buttons in vertical layout
                            current_category = news_item.get("category", "general").lower()
                            is_liked = current_category in st.session_state.liked_categories
                            
                            # Read button
                            if st.button("📄 Read Article", key=f"news_btn_{index}"):
                                st.session_state.news_detail = news_item
                                st.rerun()
                            
                            # Like button
                            btn_label = "❤️ Like" if not is_liked else "❤️ Liked"
                            btn_type = "primary" if is_liked else "secondary"
                            if st.button(btn_label, key=f"like_btn_{index}", type=btn_type):
                                # Toggle like status
                                if not is_liked:
                                    st.session_state.liked_categories.append(current_category)
                                    # Log the click for recommendations
                                    log_click(st.session_state.user["id"], news_item.get("title", ""), current_category)
                                    st.success(f"Added {current_category} to your interests!")
                                else:
                                    st.session_state.liked_categories.remove(current_category)
                                    st.info(f"Removed {current_category} from your interests.")
                                st.rerun()
                    
                    # Divider between news items
                    st.markdown("---")
            else:
                st.info("No news found for your preferences. Try selecting different topics or countries.")
            
            # Display instructions for likes
            with st.expander("ℹ️ How to use likes"):
                st.markdown("""
                **Like articles to personalize your news feed:**
                
                1. Click the ❤️ Like button on articles that interest you
                2. View related news from your liked categories when you read an article
                3. Your likes help us recommend better content for you
                """)
            
        # Show article detail view if a news item is selected
        if "news_detail" in st.session_state:
            st.markdown("---")
            render_news_detail(st.session_state.news_detail, st.session_state.user["id"])
            if st.button("⬅️ Back to Feed"):
                del st.session_state.news_detail
                st.rerun()
