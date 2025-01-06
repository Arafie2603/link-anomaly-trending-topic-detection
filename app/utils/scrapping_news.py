import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os
import re
from urllib.parse import urlparse, unquote

load_dotenv()

def convert_to_utc(local_time_str, timezone="Asia/Jakarta"):
    local_tz = pytz.timezone(timezone)
    if 'T' in local_time_str:
        local_time = datetime.strptime(local_time_str, "%Y-%m-%dT%H:%M:%S")
    else:
        local_time = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M:%S")
    local_time = local_tz.localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    return utc_time

def extract_date_from_url(url):
    """Extract date from Kompas URL format."""
    # Format URL Kompas: .../read/YYYY/MM/DD/HHMMSS/...
    date_pattern = r'/read/(\d{4})/(\d{2})/(\d{2})/(\d{2})(\d{2})(\d{2})/'
    match = re.search(date_pattern, url)
    
    if match:
        year, month, day, hour, minute, second = map(int, match.groups())
        try:
            local_tz = pytz.timezone('Asia/Jakarta')
            article_date = datetime(year, month, day, hour, minute, second)
            return local_tz.localize(article_date)
        except ValueError:
            return None
    return None

def extract_date_from_snippet(snippet):
    """Extract date from article snippet."""
    # Pattern untuk "X days ago"
    days_ago_match = re.search(r'(\d+) days? ago', snippet)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        article_date = datetime.now(pytz.UTC) - timedelta(days=days)
        return article_date
    return None

def is_within_date_range(article_date, start_date, end_date):
    """Check if article date falls within the specified range."""
    if article_date:
        # Convert all dates to UTC for comparison
        if article_date.tzinfo is None:
            local_tz = pytz.timezone('Asia/Jakarta')
            article_date = local_tz.localize(article_date)
        article_date_utc = article_date.astimezone(pytz.UTC)
        return start_date <= article_date_utc <= end_date
    return False

# Parameter API
api_key = os.getenv("GOOGLE_API")
cse_id = os.getenv("CSE_ID")
query = "pilkada site:kompas.com"

# Waktu yang diinginkan (WIB)
waktu_awal = "2024-10-30 22:39:00"
waktu_akhir = "2024-10-31 22:39:00"

# Konversi ke UTC
utc_start = convert_to_utc(waktu_awal)
utc_end = convert_to_utc(waktu_akhir)

print(f"Mencari artikel dalam rentang waktu:")
print(f"Waktu awal (WIB): {waktu_awal}")
print(f"Waktu akhir (WIB): {waktu_akhir}")

# Request ke API Google Custom Search
url = "https://www.googleapis.com/customsearch/v1"
params = {
    "key": api_key,
    "cx": cse_id,
    "q": query,
    "num": 10,
    "sort": "date",
    # Menambahkan parameter dateRestrict yang lebih longgar
    "dateRestrict": "d2"  # Mencari dalam 2 hari terakhir
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    if "items" in data:
        print("\nHasil pencarian dalam rentang waktu yang ditentukan:")
        found_articles = False
        
        for item in data["items"]:
            # Coba ekstrak tanggal dari URL terlebih dahulu
            article_date = extract_date_from_url(item['link'])
            
            # Jika tidak ada tanggal dari URL, coba dari snippet
            if not article_date:
                article_date = extract_date_from_snippet(item.get('snippet', ''))
            
            if article_date and is_within_date_range(article_date, utc_start, utc_end):
                found_articles = True
                print(f"\n- Title: {item['title']}")
                print(f"  Link: {item['link']}")
                print(f"  Snippet: {item.get('snippet', 'No snippet available')}")
                print(f"  Tanggal publikasi: {article_date.astimezone(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S WIB')}")
        
        if not found_articles:
            print("Tidak ditemukan artikel dalam rentang waktu yang ditentukan.")
            print("\nSemua artikel yang ditemukan (di luar rentang waktu):")
            for item in data["items"]:
                article_date = extract_date_from_url(item['link'])
                if article_date:
                    print(f"\n- Title: {item['title']}")
                    print(f"  Link: {item['link']}")
                    print(f"  Tanggal: {article_date.astimezone(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S WIB')}")
    else:
        print("Tidak ada hasil yang ditemukan.")
else:
    print(f"Error: {response.status_code}")
    print(response.text)