import gspread
from google.oauth2.service_account import Credentials

try:
    # Load credentials
    credentials = Credentials.from_service_account_file('credentials/google_credentials.json')
    gc = gspread.authorize(credentials)
    
    # Try to open your sheet (replace with your sheet URL)
    sheet_url = "YOUR_GOOGLE_SHEET_URL_HERE"
    sheet = gc.open_by_url(sheet_url).sheet1
    
    # Try to read data
    data = sheet.get_all_records()
    print(f"✅ Success! Found {len(data)} rows in your sheet")
    
except Exception as e:
    print(f"❌ Error: {e}")