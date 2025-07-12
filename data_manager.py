"""
Data management for aINeedToKnow - handles Google Sheets integration, caching, and hotness tracking
"""
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime, timedelta
import os
import json
from config import *

class DataManager:
    def __init__(self):
        self.gc = None
        self.sheet = None
        self.hotness_sheet = None
        self.setup_google_sheets()
        
    def setup_google_sheets(self):
        """Initialize Google Sheets connection with better error handling"""
        try:
            # Define required scopes
            SCOPES = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = None
            sheet_url = None
            
            # Method 1: Try Streamlit secrets (for deployment)
            if hasattr(st, 'secrets') and 'google_credentials' in st.secrets:
                print("🔑 Using Streamlit secrets for credentials")
                try:
                    # Convert secrets to dict and handle private key formatting
                    credentials_dict = dict(st.secrets['google_credentials'])
                    
                    # Ensure private key has proper formatting
                    if 'private_key' in credentials_dict:
                        private_key = credentials_dict['private_key']
                        # Replace literal \n with actual newlines
                        private_key = private_key.replace('\\n', '\n')
                        credentials_dict['private_key'] = private_key
                    
                    credentials = Credentials.from_service_account_info(
                        credentials_dict, 
                        scopes=SCOPES
                    )
                    sheet_url = st.secrets.get('GOOGLE_SHEET_URL', GOOGLE_SHEET_URL)
                    print("✅ Successfully loaded Streamlit secrets")
                    
                except Exception as e:
                    print(f"❌ Error with Streamlit secrets: {e}")
                    credentials = None
            
            # Method 2: Try local credentials file (for development)
            if not credentials and os.path.exists(GOOGLE_CREDENTIALS_PATH):
                print("🔑 Using local credentials file")
                try:
                    credentials = Credentials.from_service_account_file(
                        GOOGLE_CREDENTIALS_PATH,
                        scopes=SCOPES
                    )
                    sheet_url = GOOGLE_SHEET_URL
                    print("✅ Successfully loaded local credentials")
                    
                except Exception as e:
                    print(f"❌ Error with local credentials: {e}")
                    credentials = None
            
            # Method 3: Try environment variables
            if not credentials:
                try:
                    creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
                    if creds_json:
                        print("🔑 Using environment variable credentials")
                        credentials_dict = json.loads(creds_json)
                        credentials = Credentials.from_service_account_info(
                            credentials_dict,
                            scopes=SCOPES
                        )
                        sheet_url = os.getenv('GOOGLE_SHEET_URL', GOOGLE_SHEET_URL)
                        print("✅ Successfully loaded environment credentials")
                except Exception as e:
                    print(f"❌ Error with environment credentials: {e}")
            
            if not credentials:
                st.error("""
                🔧 **Google Sheets Setup Required**
                
                No valid credentials found. Please set up one of the following:
                
                **For Streamlit Cloud:**
                - Add credentials to your app's secrets in the Streamlit dashboard
                
                **For Local Development:**
                - Put `google_credentials.json` in the `credentials/` folder
                - Or set `GOOGLE_CREDENTIALS_JSON` environment variable
                
                📚 [Setup Guide](https://docs.streamlit.io/streamlit-community-cloud/deploy-an-app/connect-to-data-sources/secrets-management)
                """)
                return
            
            # Authorize and connect to Google Sheets
            print("🔐 Authorizing Google Sheets client...")
            self.gc = gspread.authorize(credentials)
            
            if sheet_url:
                print(f"📊 Connecting to sheet: {sheet_url}")
                spreadsheet = self.gc.open_by_url(sheet_url)
                self.sheet = spreadsheet.sheet1  # Main tools sheet
                
                # Setup hotness tracking sheet
                self.setup_hotness_sheet(spreadsheet)
                
                print("✅ Successfully connected to Google Sheets!")
            else:
                st.error("❌ Google Sheet URL not configured.")
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Google Sheets connection failed: {error_msg}")
            
            # Provide specific error messages
            if "invalid_grant" in error_msg.lower():
                st.error("""
                🔧 **Authentication Error: Invalid JWT Signature**
                
                This usually means there's an issue with your credentials:
                
                **Common fixes:**
                1. **Check private key formatting** - Make sure newlines are properly formatted
                2. **Verify service account email** - Ensure your Google Sheet is shared with: 
                   `aineedtoknow-reader@aineedtoknow-app.iam.gserviceaccount.com`
                3. **Check system time** - Ensure your system clock is synchronized
                4. **Regenerate credentials** - Create new service account key if needed
                
                **Current error:** `{}`
                """.format(error_msg))
            elif "permission" in error_msg.lower():
                st.error(f"""
                🔧 **Permission Error**
                
                Please share your Google Sheet with this service account email:
                `aineedtoknow-reader@aineedtoknow-app.iam.gserviceaccount.com`
                
                Give it **Editor** permissions.
                
                **Error:** {error_msg}
                """)
            else:
                st.error(f"❌ Failed to connect to Google Sheets: {error_msg}")
    
    def setup_hotness_sheet(self, spreadsheet):
        """Setup or access the hotness tracking sheet"""
        try:
            # Try to access existing Hotness sheet
            try:
                self.hotness_sheet = spreadsheet.worksheet("Hotness")
                print("✅ Found existing Hotness sheet")
            except gspread.WorksheetNotFound:
                print("📝 Creating new Hotness sheet...")
                # Create new sheet with headers
                self.hotness_sheet = spreadsheet.add_worksheet(title="Hotness", rows="1000", cols="5")
                
                # Add headers
                headers = ["Tool_Title", "IP_Address", "Timestamp", "User_Agent", "Session_ID"]
                self.hotness_sheet.append_row(headers)
                print("✅ Created Hotness sheet with headers")
                
        except Exception as e:
            print(f"⚠️ Could not setup hotness sheet: {e}")
            self.hotness_sheet = None
    
    def record_hotness_vote(self, tool_title, ip_address):
        """Record a hotness vote for a tool"""
        try:
            if not self.hotness_sheet:
                print("❌ No hotness sheet available")
                return False
            
            # Check if this IP already voted for this tool (use cache to reduce API calls)
            if self.check_if_ip_voted_cached(tool_title, ip_address):
                print(f"⚠️ IP {ip_address} already voted for {tool_title}")
                return False
            
            # Record the vote
            timestamp = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
            user_agent = "Streamlit_App"
            session_id = st.session_state.get('session_id', 'unknown')
            
            row = [tool_title, ip_address, timestamp, user_agent, session_id]
            self.hotness_sheet.append_row(row)
            
            print(f"✅ Recorded hotness vote: {tool_title} from {ip_address}")
            
            # Clear specific caches to force refresh
            self._get_cached_hotness_counts.clear()
            self._fetch_cached_data_with_hotness.clear()
            
            return True
            
        except Exception as e:
            print(f"❌ Error recording hotness vote: {e}")
            return False
    
    @st.cache_data(ttl=60, show_spinner=False)  # Cache vote status for 1 minute
    def check_if_ip_voted_cached(_self, tool_title, ip_address):
        """Cached version of IP vote check"""
        return _self.check_if_ip_voted(tool_title, ip_address)
    
    def check_if_ip_voted(self, tool_title, ip_address):
        """Check if an IP address has already voted for a specific tool"""
        try:
            if not self.hotness_sheet:
                return False
            
            # Get all hotness records
            records = self.hotness_sheet.get_all_records()
            
            # Check if this IP already voted for this tool
            for record in records:
                if (record.get('Tool_Title', '') == tool_title and 
                    record.get('IP_Address', '') == ip_address):
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error checking IP vote status: {e}")
            return False
    
    def get_hotness_counts(self):
        """Get hotness counts for all tools"""
        try:
            if not self.hotness_sheet:
                return {}
            
            # Get all hotness records
            records = self.hotness_sheet.get_all_records()
            
            # Count votes per tool
            hotness_counts = {}
            for record in records:
                tool_title = record.get('Tool_Title', '')
                if tool_title:
                    hotness_counts[tool_title] = hotness_counts.get(tool_title, 0) + 1
            
            print(f"📊 Hotness counts: {hotness_counts}")
            return hotness_counts
            
        except Exception as e:
            print(f"❌ Error getting hotness counts: {e}")
            return {}
    
    def fetch_news_data_with_hotness(self, force_refresh=False):
        """Fetch news data from Google Sheets with hotness counts"""
        # Use session state to track force refresh
        if hasattr(st.session_state, 'force_refresh') and st.session_state.force_refresh:
            force_refresh = True
            st.session_state.force_refresh = False  # Reset the flag
        
        if force_refresh:
            # Skip cache and fetch fresh data
            return self._fetch_fresh_data_with_hotness()
        else:
            # Use cached version
            return self._fetch_cached_data_with_hotness()
    
    @st.cache_data(ttl=CACHE_DURATION*3600, show_spinner=False)  # Cache for specified hours
    def _fetch_cached_data_with_hotness(_self):
        """Cached version of data fetching with hotness"""
        return _self._fetch_fresh_data_with_hotness()
    
    @st.cache_data(ttl=300, show_spinner=False)  # Cache hotness for 5 minutes
    def _get_cached_hotness_counts(_self):
        """Cached version of hotness counts to reduce API calls"""
        return _self.get_hotness_counts()
    
    def _fetch_fresh_data_with_hotness(self):
        """Fetch fresh data from Google Sheets with hotness counts"""
        try:
            # Get base news data
            df = self._fetch_fresh_data()
            
            if df.empty:
                return df
            
            # Get cached hotness counts to reduce API calls
            hotness_counts = self._get_cached_hotness_counts()
            
            # Add hotness counts to dataframe
            df['hotness_count'] = df['Title'].map(lambda title: hotness_counts.get(title, 0))
            
            print(f"✅ Added hotness data to {len(df)} tools")
            return df
            
        except Exception as e:
            print(f"❌ Error fetching data with hotness: {e}")
            # Fallback to data without hotness
            base_df = self._fetch_fresh_data()
            if not base_df.empty:
                base_df['hotness_count'] = 0
            return base_df
    
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
    
    def save_user_email_to_gsheet(self,name, email, linkedin=""):
        try:
            # Setup credentials from Streamlit secrets
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_info(st.secrets["google_credentials"], scopes=scope)
            client = gspread.authorize(creds)

            # Open the sheet by URL or name
            sheet = client.open_by_url(st.secrets["GOOGLE_SHEET_URL"])
            worksheet = sheet.worksheet("Signups")  # Make sure this tab exists

            # Get all existing emails to prevent duplicate signup
            emails = worksheet.col_values(2)  # Assuming Email is column B
            if email in emails:
                return False, "Email already registered!"

            # Prepare row
            signup_time = datetime.now().strftime('%m/%d/%Y %H:%M:%S')
            row = [name, email, linkedin, signup_time]

            # Append to the bottom of the sheet
            worksheet.append_row(row)
            return True, "Successfully registered for updates!"

        except Exception as e:
            return False, f"Error saving to Google Sheet: {str(e)}"