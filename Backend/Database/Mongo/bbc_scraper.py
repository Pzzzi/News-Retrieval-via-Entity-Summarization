import re
import threading
import requests
import os
from bs4 import BeautifulSoup
from pymongo import MongoClient
import concurrent.futures  # For parallel requests
from dotenv import load_dotenv
from dateutil import parser  # To parse date strings into datetime objects

load_dotenv()

# ====== MongoDB Connection ======
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# ====== BBC News URLs ======
URLS = [
    "https://www.bbc.com/news",
    "https://www.bbc.com/business",
    "https://www.bbc.com/innovation",
    "https://www.bbc.com/culture",
    "https://www.bbc.com/arts",
    "https://www.bbc.com/travel",
    "https://www.bbc.com/future-planet"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def is_placeholder_image(img_url):
    """Check if the image URL is a placeholder."""
    if not img_url:
        return True
    placeholder_strings = [
        "grey-placeholder.png",
        "/bbcx/grey-placeholder.png",
        "https://www.bbc.com/bbcx/grey-placeholder.png"
    ]
    return any(placeholder in img_url for placeholder in placeholder_strings)

# === Extract Full Article Text + Date + Images ===
def get_full_article(article_url):
    """Fetches full article text, publication date, and images from BBC."""
    try:
        response = requests.get(article_url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None, None, []

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract article text
        article_tag = soup.find("article")
        if not article_tag:
            return None, None, []

        paragraphs = article_tag.find_all("p")
        full_text = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])

        # Extract publication date (BBC articles use <time> tag)
        date_tag = soup.find("time")
        pub_date = date_tag["datetime"] if date_tag and "datetime" in date_tag.attrs else None

        # Parse date string into datetime object (if valid)
        if pub_date:
            try:
                pub_date = parser.parse(pub_date)  # Convert to datetime object
            except Exception as e:
                print(f"❌ Failed to parse date for {article_url}: {e}")
                pub_date = None

        # Extract images (look for <figure> tags and grab <img> tag inside them)
        img_urls = set()
        
        # Find all images within the article
        for img in article_tag.find_all('img'):
            # Check src attribute first
            if img.get('src'):
                img_url = img['src']
                if not is_placeholder_image(img_url):
                    img_urls.add(img_url)
            
            # Check srcset if exists
            if img.get('srcset'):
                # Get all URLs from srcset (take the first part before space)
                for src in img['srcset'].split(','):
                    src_url = src.strip().split(' ')[0]
                    if src_url and not is_placeholder_image(src_url):
                        img_urls.add(src_url)
        
        # Convert to absolute URLs and filter out data URIs
        final_img_urls = [
            f'https://www.bbc.com{url}' if url.startswith('/') else url
            for url in img_urls
            if not url.startswith('data:')  # Skip data URIs
        ]

        return full_text if full_text else None, pub_date, final_img_urls

    except Exception as e:
        print(f"❌ Error fetching article {article_url}: {e}")
        return None, None, []

# === Scrape Section for Article Links ===
def scrape_section(url):
    """Scrape WITHOUT database checks"""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        return [
            {"title": (article.find("h3") or article.find("h2")).text.strip(),
             "url": f"https://www.bbc.com{article['href']}" if article['href'].startswith("/") else article['href']}
            for article in soup.find_all("a", href=True)
            if article.find("h3") or article.find("h2")
        ]
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return []

# === Scrape All Sections in Parallel ===
def scrape_all_sections():
    """Thread-safe deduplication during scraping"""
    # Thread-safe storage for URLs
    seen_urls = set()
    lock = threading.Lock()
    total_saved = 0

    def process_article(article):
        nonlocal total_saved
        full_text, pub_date, img_urls = get_full_article(article['url'])
        if not full_text:
            return

        doc = {
            "title": article['title'],
            "url": article['url'],
            "content": full_text,
            "date": pub_date,
            "images": img_urls
        }

        # Atomic insert with thread-safe URL tracking
        with lock:
            clean_url = article['url'].split('?')[0]  # Remove tracking params
            if clean_url not in seen_urls:
                result = collection.update_one(
                    {"url": {"$regex": f"^{re.escape(clean_url)}"}},
                    {"$setOnInsert": doc},
                    upsert=True
                )
                if result.upserted_id:
                    seen_urls.add(clean_url)
                    total_saved += 1
                    print(f"✅ Saved: {article['title'][:50]}...")

    # Phase 1: Scrape all sections
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        all_articles = []
        for section_articles in executor.map(scrape_section, URLS):
            all_articles.extend(section_articles)

    # Phase 2: Process with thread-safe deduplication
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # Pre-populate seen_urls with existing DB entries
        existing = collection.find(
            {"url": {"$in": [a['url'] for a in all_articles]}},
            {"url": 1}
        )
        with lock:
            seen_urls.update(doc['url'].split('?')[0] for doc in existing)

        # Process articles
        executor.map(process_article, all_articles)

    print(f"🎉 Total new articles saved: {total_saved}")

# Run the scraper
scrape_all_sections()