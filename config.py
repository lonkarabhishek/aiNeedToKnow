"""
Configuration settings for aINeedToKnow app
"""
import os

# App Configuration
APP_TITLE = "aINeedToKnow"
APP_TAGLINE = "Stay ahead with AIs and up your Analytics game"

# Google Sheets Configuration
GOOGLE_SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "")  # Set this in Streamlit secrets
GOOGLE_CREDENTIALS_PATH = "credentials/google_credentials.json"

# Required Google API Scopes
GOOGLE_SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Cache Configuration (in hours)
CACHE_DURATION = 1

# Domain Categories
DOMAINS = [
    "All",
    "Analytics", 
    "Data Science (Coming Soon)",
    "Machine Learning (Coming Soon)",
    "Business Intelligence (Coming Soon)",
    "General AI (Coming Soon)"
]

# File Paths
USERS_CSV_PATH = "cache/users.csv"
NEWS_CACHE_PATH = "cache/news_cache.csv"

# UI Configuration
CARDS_PER_PAGE = 10
MOBILE_BREAKPOINT = 768

# Email Configuration (for future use)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@aineedtoknow.com")