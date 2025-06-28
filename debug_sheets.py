"""
Debug script to check what data we're getting from Google Sheets
"""
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# Use the same setup as your app
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def debug_sheets_data():
    """Debug what data we're getting from the sheet"""
    try:
        print("🔍 Debugging Google Sheets data...")
        
        # Load credentials
        credentials = Credentials.from_service_account_file(
            "credentials/google_credentials.json",
            scopes=SCOPES
        )
        
        gc = gspread.authorize(credentials)
        
        # Open your sheet
        sheet_url = "https://docs.google.com/spreadsheets/d/19tkA1F5pW4RMi_n7irzpsiNk1GPMTLf04KJP0vKGIPM/edit"
        sheet = gc.open_by_url(sheet_url).sheet1
        
        print("✅ Connected to Google Sheets")
        
        # Get all records
        print("\n📋 Getting all records...")
        records = sheet.get_all_records()
        print(f"📊 Found {len(records)} records")
        
        # Print each record
        for i, record in enumerate(records):
            print(f"\n--- Record {i+1} ---")
            for key, value in record.items():
                print(f"{key}: {value}")
        
        # Convert to DataFrame
        print("\n📈 Converting to DataFrame...")
        df = pd.DataFrame(records)
        print(f"DataFrame shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        
        # Check for empty rows
        print("\n🔍 Checking for empty/problematic rows...")
        for i, row in df.iterrows():
            title = row.get('Title', '')
            summary = row.get('Summary', '')
            print(f"Row {i+1}: Title='{title}', Summary='{summary}'")
            
            if not title or not summary:
                print(f"  ⚠️  Row {i+1} has empty Title or Summary!")
        
        # Test date parsing
        print("\n📅 Testing date parsing...")
        for i, row in df.iterrows():
            date_str = row.get('Date_Added', '')
            print(f"Row {i+1}: Date_Added='{date_str}'")
            try:
                parsed_date = pd.to_datetime(date_str, errors='coerce')
                print(f"  Parsed as: {parsed_date}")
            except Exception as e:
                print(f"  ❌ Date parsing error: {e}")
        
        return df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    debug_sheets_data()