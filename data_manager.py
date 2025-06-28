"""
Data management for aINeedToKnow - handles Google Sheets integration and caching
"""
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime, timedelta
import os
from config import *

class DataManager:
    def __init__(self):
        self.gc = None
        self.sheet = None
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Initialize Google Sheets connection"""
        try:
            # Define required scopes
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Check if running on Streamlit Cloud (using secrets)
            if hasattr(st, 'secrets') and 'google_credentials' in st.secrets:
                # Use Streamlit secrets for deployment
                credentials_dict = dict(st.secrets['google_credentials'])
                credentials = Credentials.from_service_account_info(
                    credentials_dict, 
                    scopes=SCOPES
                )
                self.gc = gspread.authorize(credentials)
                sheet_url = st.secrets.get('GOOGLE_SHEET_URL', GOOGLE_SHEET_URL)
            else:
                # Try local credentials file first
                if os.path.exists(GOOGLE_CREDENTIALS_PATH):
                    credentials = Credentials.from_service_account_file(
                        GOOGLE_CREDENTIALS_PATH,
                        scopes=SCOPES
                    )
                    self.gc = gspread.authorize(credentials)
                    sheet_url = GOOGLE_SHEET_URL
                else:
                    # Fallback: show helpful error message
                    st.error("""
                    🔧 **Google Sheets Setup Required**
                    
                    Choose one option:
                    
                    **Option 1: Streamlit Secrets (Recommended)**
                    1. Create `.streamlit/secrets.toml` file
                    2. Add your Google credentials to it
                    
                    **Option 2: Local Credentials File**
                    1. Put your `google_credentials.json` in the `credentials/` folder
                    2. Set GOOGLE_SHEET_URL in config.py
                    
                    📚 [See setup guide for details](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
                    """)
                    return
            
            # Open the Google Sheet
            if sheet_url:
                self.sheet = self.gc.open_by_url(sheet_url).sheet1
            else:
                st.error("Google Sheet URL not configured.")
                
        except Exception as e:
            st.error(f"Failed to connect to Google Sheets: {str(e)}")
            
    def fetch_news_data(self, force_refresh=False):
        """Fetch news data from Google Sheets with caching"""
        # Use session state to track force refresh
        if hasattr(st.session_state, 'force_refresh') and st.session_state.force_refresh:
            force_refresh = True
            st.session_state.force_refresh = False  # Reset the flag
        
        if force_refresh:
            # Skip cache and fetch fresh data
            return self._fetch_fresh_data()
        else:
            # Use cached version
            return self._fetch_cached_data()
    
    @st.cache_data(ttl=CACHE_DURATION*3600)  # Cache for specified hours
    def _fetch_cached_data(_self):
        """Cached version of data fetching"""
        return _self._fetch_fresh_data()
    
    def _fetch_fresh_data(self):
        """Fetch fresh data from Google Sheets without caching"""
        try:
            if not self.sheet:
                print("❌ No sheet connection")
                return pd.DataFrame()
                
            # Get all records from the sheet
            print("📥 Fetching records from Google Sheets...")
            records = self.sheet.get_all_records()
            print(f"📊 Retrieved {len(records)} records from Google Sheets")
            
            if not records:
                print("⚠️ No records found in sheet")
                return pd.DataFrame()
                
            df = pd.DataFrame(records)
            print(f"📈 Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
            print(f"🔤 Columns: {list(df.columns)}")
            
            # Clean and validate data
            df = self._clean_data(df)
            
            # Save to local cache
            self._save_to_cache(df)
            
            print(f"✅ Returning {len(df)} cleaned records")
            return df
            
        except Exception as e:
            print(f"❌ Error in _fetch_fresh_data: {str(e)}")
            st.error(f"Error fetching data from Google Sheets: {str(e)}")
            # Try to load from local cache as fallback
            return self._load_from_cache()
    
    def _clean_data(self, df):
        """Clean and validate the data"""
        print(f"🧹 Cleaning data: {len(df)} rows before cleaning")
        
        # Ensure required columns exist
        required_columns = ['Title', 'Summary', 'Source_URL', 'Author/Company', 'Domain', 'Integration_Steps', 'Date_Added']
        
        for col in required_columns:
            if col not in df.columns:
                df[col] = ''
                print(f"⚠️ Missing column '{col}' - added empty column")
        
        # Debug: print before filtering
        print("📊 Data before filtering:")
        for i, row in df.iterrows():
            title = str(row.get('Title', '')).strip()
            summary = str(row.get('Summary', '')).strip()
            print(f"  Row {i+1}: Title='{title}' ({len(title)} chars), Summary='{summary}' ({len(summary)} chars)")
        
        # Filter out rows with empty titles or summaries (but be more lenient)
        df_filtered = df[
            (df['Title'].astype(str).str.strip() != '') & 
            (df['Title'].astype(str).str.strip() != 'nan') &
            (df['Summary'].astype(str).str.strip() != '') & 
            (df['Summary'].astype(str).str.strip() != 'nan')
        ].copy()
        
        print(f"🔍 After filtering empty titles/summaries: {len(df_filtered)} rows")
        
        # Convert date format and handle errors gracefully
        print("📅 Processing dates...")
        df_filtered['Date_Added'] = pd.to_datetime(df_filtered['Date_Added'], errors='coerce')
        
        # If date parsing failed, use current date
        null_dates = df_filtered['Date_Added'].isnull().sum()
        if null_dates > 0:
            print(f"⚠️ {null_dates} rows had invalid dates, using current date")
            df_filtered.loc[df_filtered['Date_Added'].isnull(), 'Date_Added'] = datetime.now()
        
        # Sort by date (newest first)
        df_filtered = df_filtered.sort_values('Date_Added', ascending=False)
        
        print(f"✅ Final cleaned data: {len(df_filtered)} rows")
        return df_filtered
    
    def _save_to_cache(self, df):
        """Save data to local cache"""
        try:
            os.makedirs('cache', exist_ok=True)
            df.to_csv(NEWS_CACHE_PATH, index=False)
        except Exception as e:
            st.warning(f"Could not save to cache: {str(e)}")
    
    def _load_from_cache(self):
        """Load data from local cache as fallback"""
        try:
            if os.path.exists(NEWS_CACHE_PATH):
                df = pd.read_csv(NEWS_CACHE_PATH)
                df['Date_Added'] = pd.to_datetime(df['Date_Added'], errors='coerce')
                return df
            else:
                return pd.DataFrame()
        except Exception as e:
            st.error(f"Could not load from cache: {str(e)}")
            return pd.DataFrame()
    
    def filter_by_domain(self, df, selected_domain):
        """Filter data by selected domain"""
        if selected_domain == "All" or selected_domain == "":
            return df
        
        return df[df['Domain'].str.contains(selected_domain, case=False, na=False)]
    
    def filter_by_date_range(self, df, days=7):
        """Filter data by date range (last N days)"""
        if df.empty:
            return df
            
        cutoff_date = datetime.now() - timedelta(days=days)
        return df[df['Date_Added'] >= cutoff_date]
    
    def get_recent_news(self, domain="All", days=7):
        """Get recent news filtered by domain and date"""
        df = self.fetch_news_data()
        
        if df.empty:
            return df
            
        # Filter by date range
        df = self.filter_by_date_range(df, days)
        
        # Filter by domain
        df = self.filter_by_domain(df, domain)
        
        return df
    
    def get_unique_domains(self):
        """Get unique domains from the data"""
        try:
            df = self._fetch_fresh_data()
            if df.empty:
                return ["All", "Analytics"]
            
            # Get unique domains and sort them
            unique_domains = sorted(df['Domain'].dropna().unique().tolist())
            
            # Always include "All" at the beginning
            domains = ["All"] + unique_domains
            
            # Remove duplicates while preserving order
            seen = set()
            result = []
            for domain in domains:
                if domain not in seen:
                    seen.add(domain)
                    result.append(domain)
            
            return result
            
        except Exception as e:
            print(f"Error getting unique domains: {e}")
            return ["All", "Analytics"]
        """Save user email to CSV file"""
        try:
            os.makedirs('cache', exist_ok=True)
            
            # Create user data
            user_data = {
                'Name': name,
                'Email': email,
                'LinkedIn': linkedin,
                'Signup_Date': datetime.now().strftime('%m/%d/%Y %H:%M:%S')
            }
            
            # Check if file exists
            if os.path.exists(USERS_CSV_PATH):
                users_df = pd.read_csv(USERS_CSV_PATH)
                # Check if email already exists
                if email in users_df['Email'].values:
                    return False, "Email already registered!"
                
                # Append new user
                users_df = pd.concat([users_df, pd.DataFrame([user_data])], ignore_index=True)
            else:
                users_df = pd.DataFrame([user_data])
            
            # Save to CSV
            users_df.to_csv(USERS_CSV_PATH, index=False)
            return True, "Successfully registered for daily updates!"
            
        except Exception as e:
            return False, f"Error saving user data: {str(e)}"
    def save_user_email(self, name, email, linkedin=""):
            """Save user email to CSV file"""
            try:
                os.makedirs('cache', exist_ok=True)
                
                # Create user data
                user_data = {
                    'Name': name,
                    'Email': email,
                    'LinkedIn': linkedin,
                    'Signup_Date': datetime.now().strftime('%m/%d/%Y %H:%M:%S')
                }
                
                # Check if file exists
                if os.path.exists(USERS_CSV_PATH):
                    users_df = pd.read_csv(USERS_CSV_PATH)
                    # Check if email already exists
                    if email in users_df['Email'].values:
                        return False, "Email already registered!"
                    
                    # Append new user
                    users_df = pd.concat([users_df, pd.DataFrame([user_data])], ignore_index=True)
                else:
                    users_df = pd.DataFrame([user_data])
                
                # Save to CSV
                users_df.to_csv(USERS_CSV_PATH, index=False)
                return True, "Successfully registered for updates!"
                
            except Exception as e:
                return False, f"Error saving user data: {str(e)}"