"""
aINeedToKnow - AI News Webapp for Analytics Professionals
Main Streamlit Application with Hotness Feature
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import time
import os
import hashlib
from data_manager import DataManager
from config import *

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="aineedtoknowlogo.png",  # Use your logo as favicon
    layout="wide",
    initial_sidebar_state="collapsed"
)

def get_client_ip():
    """Get client IP address for hotness tracking with browser fingerprinting"""
    try:
        # Try to get real IP from headers (for deployed apps)
        if hasattr(st, 'session_state') and hasattr(st.session_state, '_get_widget_value'):
            # In Streamlit Cloud, try to get real IP
            import streamlit.web.server.websocket_headers as wsh
            headers = wsh.get_websocket_headers()
            if headers and 'x-forwarded-for' in headers:
                real_ip = headers['x-forwarded-for'].split(',')[0].strip()
                # Store real IP in session state for consistency
                st.session_state.client_ip = real_ip
                return real_ip
            elif headers and 'x-real-ip' in headers:
                real_ip = headers['x-real-ip']
                st.session_state.client_ip = real_ip
                return real_ip
        
        # Enhanced fingerprinting for local/dev environments
        if 'client_ip' not in st.session_state:
            # Create a more stable fingerprint using browser characteristics
            import time
            import hashlib
            
            # Use browser session + timestamp to create unique but persistent ID
            browser_data = f"{st.session_state.get('session_id', 'unknown')}_{int(time.time() / 3600)}"  # Changes every hour
            fingerprint = hashlib.md5(browser_data.encode()).hexdigest()[:16]
            st.session_state.client_ip = f"dev_{fingerprint}"
        
        return st.session_state.client_ip
    except Exception as e:
        print(f"Error getting client IP: {e}")
        # Final fallback - create persistent session ID
        if 'client_ip' not in st.session_state:
            import hashlib
            import time
            fallback_id = hashlib.md5(f"fallback_{time.time()}".encode()).hexdigest()[:16]
            st.session_state.client_ip = f"session_{fallback_id}"
        return st.session_state.client_ip

# Custom CSS for mobile-friendly design and hotness feature
st.markdown("""
<style>
    /* Remove top padding and margins */
    .main > div {
        padding-top: 0.2rem;
        padding-bottom: 2rem;
    }
    
    /* Reduce header spacing */
    .block-container {
        padding-top: 0.2rem;
        padding-bottom: 0rem;
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        padding: 0.2rem 0;
        margin-bottom: 0.5rem;
    }
    
    /* Beautiful selectbox styling */
    .stSelectbox > div > div {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        font-size: 1.1rem;
        font-weight: 500;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }
    
    .stSelectbox > div > div > div {
        color: #1a202c;
        font-weight: 600;
    }
    
    /* Hotness button styling - ONLY for fire buttons */
    .hotness-container {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        padding-right: 0px;
        margin-right: -10px;
    }
    
    .hotness-container .stButton > button {
        background: none !important;
        border: none !important;
        cursor: pointer !important;
        font-size: 2rem !important;
        transition: all 0.4s ease !important;
        padding: 12px !important;
        border-radius: 50% !important;
        position: relative !important;
        box-shadow: none !important;
    }
    
    .hotness-container .stButton > button:hover {
        transform: scale(1.6) rotate(15deg) !important;
        filter: drop-shadow(0 6px 12px rgba(255, 107, 107, 0.8)) !important;
        animation: fireGlow 0.6s ease-in-out infinite alternate !important;
        background: radial-gradient(circle, rgba(255,107,107,0.2) 0%, transparent 70%) !important;
    }
    
    .hotness-container .stButton > button:focus {
        box-shadow: none !important;
        outline: none !important;
    }
    
    @keyframes fireGlow {
        from {
            filter: drop-shadow(0 6px 12px rgba(255, 107, 107, 0.6));
        }
        to {
            filter: drop-shadow(0 8px 16px rgba(255, 165, 0, 1));
        }
    }
    
    .hotness-container .stButton > button[disabled] {
        opacity: 0.7 !important;
        cursor: default !important;
        transform: scale(1.1) !important;
    }
    
    .hotness-container .stButton > button[disabled]:hover {
        transform: scale(1.2) !important;
        animation: none !important;
    }
    
    /* Voted state fire emoji */
    .voted-fire {
        font-size: 2rem;
        opacity: 0.4;
        padding: 12px;
        cursor: pointer;
        transition: opacity 0.3s ease;
    }
    
    .voted-fire:hover {
        opacity: 0.6;
    }
    
    /* Fire celebration animation */
    @keyframes fireExplosion {
        0% {
            opacity: 1;
            transform: translateY(0) scale(1) rotate(0deg);
        }
        50% {
            opacity: 0.8;
            transform: translateY(-30px) scale(1.3) rotate(180deg);
        }
        100% {
            opacity: 0;
            transform: translateY(-60px) scale(0.5) rotate(360deg);
        }
    }
    
    .fire-celebration {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 100;
        overflow: hidden;
    }
    
    .fire-emoji {
        position: absolute;
        font-size: 1.5rem;
        animation: fireExplosion 2s ease-out forwards;
    }
    
    /* Hotness progress bar */
    .hotness-bar {
        width: 60px;
        height: 4px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 2px;
        overflow: hidden;
        margin-top: 4px;
    }
    
    .hotness-progress {
        height: 100%;
        background: linear-gradient(90deg, #ffd89b 0%, #19547b 100%);
        border-radius: 2px;
        transition: width 0.3s ease;
    }
    
    /* Spotlight styling for hottest tool */
    .spotlight-container {
        margin-bottom: 2rem;
    }
    
    .spotlight-tile {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: 3px solid #ffd700;
        box-shadow: 0 12px 30px rgba(255, 215, 0, 0.4);
        position: relative;
        overflow: hidden;
        border-radius: 12px;
        margin: 0 auto;
        max-width: 600px;
    }
    
    .spotlight-badge {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #1a202c;
        padding: 8px 20px;
        text-align: center;
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 1rem;
        border-radius: 0 0 20px 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .spotlight-tile .main-title {
        color: white !important;
    }
    
    .spotlight-tile .content-text {
        color: rgba(255, 255, 255, 0.9) !important;
    }
    
    /* Scroll indicator */
    .scroll-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.7rem 1.2rem;
        border-radius: 25px;
        font-size: 0.9rem;
        font-weight: 500;
        z-index: 1000;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        animation: fadeIn 0.3s ease;
        cursor: pointer;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .scroll-indicator:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    
    .logo-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 2rem;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: bold;
        color: #1E3A8A;
        margin-bottom: 0.5rem;
    }
    
    .tagline {
        font-size: 1.2rem;
        color: #6B7280;
        margin-bottom: 1rem;
    }
    
    /* Email signup form */
    .email-signup {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-top: 3rem;
        text-align: center;
    }
    
    .signup-title {
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .signup-subtitle {
        margin-bottom: 1.5rem;
        opacity: 0.9;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2rem;
        }
        
        .tagline {
            font-size: 1rem;
        }
        
        .hotness-container {
            top: 10px;
            right: 10px;
        }
        
        .hotness-button {
            padding: 6px 10px;
            font-size: 1rem;
        }
        
        .hotness-bar {
            width: 40px;
        }
    }
    
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

def add_scroll_to_refresh():
    """Add scroll-to-refresh functionality"""
    st.markdown("""
    <div id="scroll-to-refresh" style="position: fixed; top: 20px; right: 20px; 
                                     background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                     color: white; padding: 0.7rem 1.2rem; border-radius: 25px; 
                                     font-size: 0.9rem; font-weight: 500; z-index: 1000; 
                                     box-shadow: 0 4px 15px rgba(0,0,0,0.2); 
                                     display: none; cursor: pointer; transition: all 0.3s ease;">
        ↑ Scroll to top to refresh
    </div>
    
    <script>
    let lastScrollTop = 0;
    let ticking = false;
    
    function updateScrollIndicator() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        const indicator = document.getElementById('scroll-to-refresh');
        
        if (scrollTop > 100) {
            indicator.style.display = 'block';
            indicator.style.animation = 'fadeIn 0.3s ease';
        } else {
            indicator.style.display = 'none';
        }
        
        // Check if user scrolled to the very top after scrolling down
        if (scrollTop === 0 && lastScrollTop > 100) {
            // Trigger a subtle refresh animation
            indicator.innerHTML = '✨ Refreshing...';
            setTimeout(() => {
                indicator.innerHTML = '↑ Scroll to top to refresh';
            }, 1000);
        }
        
        lastScrollTop = scrollTop;
        ticking = false;
    }
    
    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(updateScrollIndicator);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestTick);
    
    // Click to scroll to top
    document.getElementById('scroll-to-refresh').addEventListener('click', function() {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    </script>
    """, unsafe_allow_html=True)

def render_header():
    """Render compact beautiful text-only header"""
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 1rem; padding: 1rem 0 0.5rem 0;">
        <h1 style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                   background-clip: text; font-size: 2.8rem; font-weight: 800; 
                   margin-bottom: 0.3rem; letter-spacing: -1px; margin-top: 0;">
            aI<span style="color: #1E3A8A;">Need</span>ToKnow
        </h1>
        <p style="color: #6B7280; font-size: 1rem; margin-bottom: 0; margin-top: 0;
                  font-weight: 400; opacity: 0.8;">
            {APP_TAGLINE}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_filters(dm):
    """Render clean filter with daily updates button"""
    
    # Get unique domains from the data
    available_domains = dm.get_unique_domains()
    
    # Check if domain filter was set by clicking a tile
    if 'selected_domain_filter' in st.session_state:
        try:
            default_index = available_domains.index(st.session_state.selected_domain_filter)
        except ValueError:
            default_index = 0
        # Clear the session state filter after using it
        del st.session_state.selected_domain_filter
    else:
        default_index = 0
    
    # Create clean filter row with better alignment
    col1, col2 = st.columns([1, 1])
    
    with col1:
        selected_domain = st.selectbox(
            "🔍 Filter by Domain",
            available_domains,
            index=default_index,
            help="Choose a domain to filter AI tools"
        )
    
    return selected_domain, 30  # Default to 30 days since we removed time filter

def calculate_hotness_score(hotness_count, max_hotness):
    """Calculate hotness percentage for progress bar - DEPRECATED"""
    # This function is no longer used since we removed the progress bar
    return 0

def render_news_feed(dm, selected_domain, selected_days):
    """Render the news feed with spotlight layout and pagination"""
    st.markdown("---")
    
    # Extract the actual domain name (remove "Coming Soon" text if any)
    actual_domain = selected_domain.split(" (Coming Soon)")[0] if selected_domain else "All"
    
    # Check if we should force refresh
    force_refresh = hasattr(st.session_state, 'force_refresh') and st.session_state.force_refresh
    
    # Fetch and filter data with hotness
    with st.spinner("Loading latest AI tools with hotness..."):
        df = dm.fetch_news_data_with_hotness(force_refresh=force_refresh)
    
    if df.empty:
        st.info(f"No tools found for {actual_domain}. Check back soon! 🚀")
        return
    
    # Filter by domain (only if not "All")
    if actual_domain != "All":
        df = dm.filter_by_domain(df, actual_domain)
    
    if df.empty:
        st.info(f"No tools found for {actual_domain}. Try selecting 'All' to see all available tools! 🔍")
        return
    
    # Sort by hotness (hottest first), then by date
    df = df.sort_values(['hotness_count', 'Date_Added'], ascending=[False, False])
    
    # Calculate max hotness for progress bars
    max_hotness = df['hotness_count'].max() if len(df) > 0 else 0
    
    # Check if we have a spotlight tool (5+ votes)
    has_spotlight = len(df) > 0 and df.iloc[0]['hotness_count'] >= 5
    
    # Display tools count
    st.markdown(f"""
    ### 🤖 {len(df)} AI Tools & Insights
    <div style="color: #6B7280; margin-bottom: 1rem;">
        Sorted by hotness 🔥 • Most tempting tools first
    </div>
    """, unsafe_allow_html=True)
    
    # Render spotlight tool if available
    if has_spotlight:
        st.markdown('<div class="spotlight-container">', unsafe_allow_html=True)
        
        # Spotlight badge
        st.markdown("""
        <div class="spotlight-badge">
            🏆 MOST TEMPTING AI TOOL • People can't resist trying this!
        </div>
        """, unsafe_allow_html=True)
        
        # Render spotlight tool in center
        spotlight_tool = df.iloc[0]
        render_ai_tile(spotlight_tool, 0, dm, max_hotness, is_spotlight=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Remove spotlight tool from regular grid
        remaining_df = df.iloc[1:].copy().reset_index(drop=True)
        start_idx = 1  # Start indexing from 1 since spotlight tool is 0
    else:
        remaining_df = df.copy()
        start_idx = 0
    
    # Pagination setup for remaining tools
    tools_per_page = 30
    total_tools = len(remaining_df)
    
    if total_tools > 0:
        total_pages = (total_tools - 1) // tools_per_page + 1
        
        # Initialize page number in session state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        
        # Reset to page 1 if domain changes
        if 'last_selected_domain' not in st.session_state:
            st.session_state.last_selected_domain = actual_domain
        elif st.session_state.last_selected_domain != actual_domain:
            st.session_state.current_page = 1
            st.session_state.last_selected_domain = actual_domain
        
        # Ensure current page is valid
        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages
        if st.session_state.current_page < 1:
            st.session_state.current_page = 1
        
        # Calculate start and end indices for current page
        page_start = (st.session_state.current_page - 1) * tools_per_page
        page_end = min(page_start + tools_per_page, total_tools)
        
        # Display pagination info
        if has_spotlight:
            st.markdown(f"""
            <div style="color: #6B7280; margin-bottom: 1rem; margin-top: 2rem;">
                Showing {page_start + 1}-{page_end} of {total_tools} additional tools 
                (Page {st.session_state.current_page} of {total_pages})
            </div>
            """, unsafe_allow_html=True)
        
        # Get current page data
        current_page_df = remaining_df.iloc[page_start:page_end].copy().reset_index(drop=True)
        
        # Create grid layout for tiles (2 columns)
        for i in range(0, len(current_page_df), 2):
            cols = st.columns(2)
            
            # First tile
            tile_idx = start_idx + page_start + i
            with cols[0]:
                render_ai_tile(current_page_df.iloc[i], tile_idx, dm, max_hotness, is_spotlight=False)
            
            # Second tile (if exists)
            if i + 1 < len(current_page_df):
                tile_idx = start_idx + page_start + i + 1
                with cols[1]:
                    render_ai_tile(current_page_df.iloc[i + 1], tile_idx, dm, max_hotness, is_spotlight=False)
        
        # Pagination controls at bottom
        if total_pages > 1:
            st.markdown("---")
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.button("⏮️ First", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page = 1
                    st.rerun()
            
            with col2:
                if st.button("◀️ Previous", disabled=(st.session_state.current_page == 1)):
                    st.session_state.current_page -= 1
                    st.rerun()
            
            with col3:
                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem; color: #6B7280; font-weight: 500;">
                    Page {st.session_state.current_page} of {total_pages}
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                if st.button("Next ▶️", disabled=(st.session_state.current_page == total_pages)):
                    st.session_state.current_page += 1
                    st.rerun()
            
            with col5:
                if st.button("Last ⏭️", disabled=(st.session_state.current_page == total_pages)):
                    st.session_state.current_page = total_pages
                    st.rerun()

def render_ai_tile(row, idx, dm, max_hotness, is_spotlight=False):
    """Render individual AI tile card with hotness feature"""
    
    # Clean data
    title = row.get('Title', 'No Title')
    summary = row.get('Summary', 'No summary available')
    source_url = row.get('Source_URL', '')
    author = row.get('Author/Company', 'Unknown')
    domain = row.get('Domain', 'General')
    integration_steps = row.get('Integration_Steps', '')
    date_added = row.get('Date_Added', '')
    hotness_count = row.get('hotness_count', 0)
    
    # Format date
    try:
        if pd.notna(date_added):
            date_str = pd.to_datetime(date_added).strftime('%m/%d/%Y')
        else:
            date_str = 'Recent'
    except:
        date_str = 'Recent'
    
    # Create short summary (first 20 words)
    words = summary.split()
    short_summary = ' '.join(words[:20])
    show_see_more = len(words) > 20
    
    # Define color scheme for different domains
    domain_colors = {
        'Data Preparation & Automation': '#667eea',
        'Spreadsheets & Documents': '#38ef7d', 
        'Code Generation & Debugging': '#ff6b6b',
        'Dashboards & Reports': '#4ecdc4',
        'Natural Language Queries': '#45b7d1',
        'AutoML & Predictive Analytics': '#6c5ce7',
        'Meetings': '#fd79a8'
    }
    
    domain_color = domain_colors.get(domain, "#667eea")
    
    # Unique key for each tile
    tile_key = f"tile_{idx}"
    
    # Initialize session state
    if f"{tile_key}_flipped" not in st.session_state:
        st.session_state[f"{tile_key}_flipped"] = False
    if f"{tile_key}_expanded" not in st.session_state:
        st.session_state[f"{tile_key}_expanded"] = False
    
    # Get client IP and check if already voted
    client_ip = get_client_ip()
    has_voted = dm.check_if_ip_voted_cached(title, client_ip)
    
    # Calculate hotness percentage - no longer needed
    # hotness_percentage = calculate_hotness_score(hotness_count, max_hotness) if max_hotness > 0 else 0
    
    # Container with spotlight styling if applicable
    container_class = "spotlight-tile" if is_spotlight else ""
    
    # Use Streamlit's built-in container with border
    with st.container(border=True):
        # Add spotlight styling with CSS injection if needed
        if is_spotlight:
            st.markdown(f"""
            <style>
            div[data-testid="stContainer"] > div:last-child {{
                background: linear-gradient(135deg, {domain_color} 0%, #764ba2 100%);
                border: 3px solid #ffd700;
                box-shadow: 0 8px 25px rgba(255, 215, 0, 0.3);
                position: relative;
                border-radius: 12px;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            # Spotlight badge
            st.markdown("""
            <div style="text-align: center; background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%); 
                       color: #1a202c; padding: 4px 12px; border-radius: 0 0 12px 12px; 
                       font-size: 0.8rem; font-weight: 700; margin: -1rem -1rem 1rem -1rem;">
                🌟 HOTTEST AI TOOL
            </div>
            """, unsafe_allow_html=True)
        
        if not st.session_state[f"{tile_key}_flipped"]:
            # Front of the card with hotness button
            
            # Create a container for title and hotness button
            col_title, col_hotness = st.columns([4, 1])
            
            with col_title:
                # Title with plain white/black styling
                if is_spotlight:
                    title_color = "#ffffff"  # Pure white for spotlight
                else:
                    title_color = "#ffffff"  # Pure white for all titles
                
                st.markdown(f"""
                <h2 style="color: {title_color} !important; font-size: 1.5rem; font-weight: 700; 
                           margin-bottom: 1rem; position: relative;" id="title_{idx}">
                    🤖 {title}
                </h2>
                """, unsafe_allow_html=True)
            
            with col_hotness:
                # Create tooltip text
                if hotness_count == 0:
                    tooltip_text = "If you're tempted to try this AI, hit this button"
                elif hotness_count == 1:
                    tooltip_text = "If you're tempted to try this AI, hit this button • 1 person clicked this today"
                else:
                    tooltip_text = f"If you're tempted to try this AI, hit this button • {hotness_count} people clicked this today"
                
                # Container for right-aligned fire button
                st.markdown('<div class="hotness-container">', unsafe_allow_html=True)
                
                # Use only Streamlit button with enhanced interactivity
                if not has_voted:
                    # Create a unique key for the button
                    button_key = f"hotness_btn_{idx}_{title[:10]}"
                    
                    if st.button("🔥", key=button_key, help=tooltip_text, use_container_width=False):
                        success = dm.record_hotness_vote(title, client_ip)
                        if success:
                            st.success("🔥 Marked as hot!")
                            # Longer delay to let user see the success message
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Already voted or error occurred")
                else:
                    # Show low opacity fire emoji for voted state
                    st.markdown(f"""
                    <div style="text-align: right; margin-right: -10px;">
                        <span class="voted-fire" title="Thank you for showing interest">🔥</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Summary with styled text (only summary gets domain color)
            current_summary = summary if st.session_state[f"{tile_key}_expanded"] else short_summary
            if show_see_more and not st.session_state[f"{tile_key}_expanded"]:
                current_summary += "..."
            
            # Apply domain color only to summary text
            text_color = domain_color
            st.markdown(f"""
            <div style="color: {text_color}; line-height: 1.6; margin-bottom: 1.2rem; font-size: 1rem;">
                {current_summary}
            </div>
            """, unsafe_allow_html=True)
            
            # Meta information in columns with colors
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style="margin-bottom: 0.8rem;">
                    <span style="color: #2d3748; font-weight: 600;">Domain:</span>
                    <span style="color: {domain_color}; font-weight: 500; 
                                background: {domain_color}15; padding: 2px 8px; 
                                border-radius: 12px; margin-left: 8px;">
                        {domain}
                    </span>
                </div>
                <div>
                    <span style="color: #2d3748; font-weight: 600;">Author:</span>
                    <span style="color: #718096; margin-left: 8px;">{author}</span>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="margin-bottom: 0.8rem;">
                    <span style="color: #2d3748; font-weight: 600;">Date:</span>
                    <span style="color: #718096; margin-left: 8px;">📅 {date_str}</span>
                </div>
                """, unsafe_allow_html=True)
                
                if source_url and str(source_url).strip():
                    st.link_button("🔗 Visit Tool", source_url, use_container_width=True)
            
            # Separator
            st.divider()
            
            # Action buttons in equal columns with colors
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if show_see_more:
                    btn_text = "📖 Read Less" if st.session_state[f"{tile_key}_expanded"] else "📖 Read More"
                    if st.button(btn_text, key=f"{tile_key}_summary", use_container_width=True, type="secondary"):
                        st.session_state[f"{tile_key}_expanded"] = not st.session_state[f"{tile_key}_expanded"]
                        st.rerun()
            
            with btn_col2:
                if st.button("How to Integrate?", key=f"{tile_key}_integrate", use_container_width=True, type="primary"):
                    st.session_state[f"{tile_key}_flipped"] = True
                    st.rerun()
            
            with btn_col3:
                if st.button(f"🔍 {domain}", key=f"{tile_key}_filter", use_container_width=True):
                    st.session_state.selected_domain_filter = domain
                    st.rerun()
        
        else:
            # Back of the card (Integration steps) with colorful styling
            
            st.markdown(f"""
            <h3 style="color: {domain_color}; font-size: 1.4rem; font-weight: 700; 
                       margin-bottom: 1rem;">
                🚀 How to Integrate: {title}
            </h3>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <h4 style="color: #2d3748; font-weight: 600; margin-bottom: 1rem;">
                📋 Integration Steps:
            </h4>
            """, unsafe_allow_html=True)
            
            if integration_steps and str(integration_steps).strip():
                # Process integration steps with colors
                steps = str(integration_steps).strip().split('\n')
                for i, step in enumerate(steps):
                    if step.strip():
                        step_color = domain_color if i % 2 == 0 else '#6B7280'
                        st.markdown(f"""
                        <div style="color: {step_color}; margin-bottom: 0.5rem; 
                                   padding-left: 1rem; font-weight: 500;">
                            • {step.strip()}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Integration steps will be available soon.")
            
            if source_url and str(source_url).strip():
                st.markdown(f"""
                <div style="margin-top: 1.5rem;">
                    <span style="color: #2d3748; font-weight: 600;">🔗 Source:</span>
                    <a href="{source_url}" target="_blank" 
                       style="color: {domain_color}; text-decoration: none; margin-left: 8px;">
                        {source_url}
                    </a>
                </div>
                """, unsafe_allow_html=True)
            
            # Separator
            st.divider()
            
            # Back button
            if st.button("← Back to Overview", key=f"{tile_key}_back", use_container_width=True, type="secondary"):
                st.session_state[f"{tile_key}_flipped"] = False
                st.rerun()

def render_email_signup(dm):
    """Render email signup form"""
    st.markdown("---")
    
    st.markdown("""
    <div class="email-signup">
        <div class="signup-title">📧 Get Regular AIs to stay upfront in your Analytics game</div>
        <div class="signup-subtitle">Join Analytical professionals staying at the forefront of AIs</div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("email_signup_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Name (Optional)", placeholder="Your name")
            email = st.text_input("Email *", placeholder="your.email@company.com")
        
        with col2:
            linkedin = st.text_input("LinkedIn (Optional)", placeholder="linkedin.com/in/yourprofile")
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        
        submitted = st.form_submit_button("🚀 Subscribe to Regular Updates", use_container_width=True)
        
        if submitted:
            if email and "@" in email and "." in email:
                try:
                    success, message = dm.save_user_email_to_gsheet(name, email, linkedin)
                    if success:
                        st.success(message)
                        st.balloons()
                    else:
                        st.warning(message)
                except Exception as e:
                    st.error(f"Error saving email: {str(e)}")
            else:
                st.error("Please enter a valid email address.")

def render_footer():
    """Render footer with expansion message"""
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6B7280; padding: 2rem 0;">
       Built with ❤️ for Work Professionals by <a href="https://www.linkedin.com/in/lonkarabhishek/" target="_blank" style="text-decoration: none; color: #667eea; font-weight: 600;">
            Abhishek Lonkar </a>
        <br><br>
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 1rem 2rem; border-radius: 12px; 
                    display: inline-block; margin-top: 1rem;">
            🚀 <strong>Coming Soon:</strong> Expanding to Data Science, Machine Learning, Sales, Marketing & more professional verticals
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    
    # Initialize data manager
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    dm = st.session_state.data_manager
    
    # Add scroll-to-refresh functionality
    add_scroll_to_refresh()
    
    # Header Section
    render_header()
    
    # Filters Section (removed time filter and refresh button)
    selected_domain, selected_days = render_filters(dm)
    
    # News Feed Section
    render_news_feed(dm, selected_domain, selected_days)
    
    # Email Signup Section
    render_email_signup(dm)
    
    # Footer
    render_footer()

if __name__ == "__main__":
    main()