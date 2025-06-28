"""
Simple test to check Google Sheets API connection
"""
import gspread
from google.oauth2.service_account import Credentials
import os

# Define the correct scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def test_connection():
    """Test Google Sheets API connection"""
    try:
        print("🔍 Testing Google Sheets API connection...")
        
        # Path to your credentials file
        creds_path = "credentials/google_credentials.json"
        
        # Check if file exists
        if not os.path.exists(creds_path):
            print(f"❌ Credentials file not found at: {creds_path}")
            print("📁 Current directory contents:")
            print(os.listdir("."))
            if os.path.exists("credentials"):
                print("📁 Credentials folder contents:")
                print(os.listdir("credentials"))
            return False
        
        # Load credentials with proper scopes
        print("🔑 Loading credentials...")
        credentials = Credentials.from_service_account_file(
            creds_path,
            scopes=SCOPES
        )
        
        # Authorize gspread client
        print("🔐 Authorizing gspread client...")
        gc = gspread.authorize(credentials)
        
        # Test basic functionality
        print("📋 Testing basic functionality...")
        spreadsheets = gc.openall()
        print(f"✅ SUCCESS! Found {len(spreadsheets)} accessible spreadsheets")
        
        # Print spreadsheet names (first 5)
        if spreadsheets:
            print("📄 Your accessible spreadsheets:")
            for i, sheet in enumerate(spreadsheets[:5]):
                print(f"  {i+1}. {sheet.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        print("\n🔧 Common fixes:")
        print("1. Make sure both Google Sheets API AND Google Drive API are enabled")
        print("2. Check if service account email is shared with your Google Sheet")
        print("3. Verify credentials file path and contents")
        return False

if __name__ == "__main__":
    test_connection()