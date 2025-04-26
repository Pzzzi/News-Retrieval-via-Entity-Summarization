import requests
import os
from bs4 import BeautifulSoup
from pymongo import MongoClient
import concurrent.futures  # For parallel requests
import time
import re
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
    """Scrapes article titles & URLs from BBC section pages."""
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Skipping {url}, status code: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        articles = soup.find_all("a", href=True)
        article_list = []

        for article in articles:
            title_tag = article.find("h3") or article.find("h2")
            if title_tag:
                title = title_tag.text.strip()
                link = f"https://www.bbc.com{article['href']}" if article['href'].startswith("/") else article['href']

                # Skip if the article already exists in MongoDB
                if collection.count_documents({"url": link}) == 0:
                    article_list.append({"title": title, "url": link})
        return article_list
    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return []

# === Scrape All Sections in Parallel ===
def scrape_all_sections():
    """Main scraping function with enhanced deduplication"""
    total_articles_saved = 0
    
    # First pass: Collect all article links with URL cleaning
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {executor.submit(scrape_section, url): url for url in URLS}
        unique_articles = {}
        
        for future in concurrent.futures.as_completed(future_to_url):
            try:
                section_articles = future.result()
                for article in section_articles:
                    # Clean URL by removing tracking parameters and fragments
                    clean_url = article['url'].split('?')[0].split('#')[0]
                    if clean_url not in unique_articles:
                        unique_articles[clean_url] = article
            except Exception as e:
                print(f"❌ Section error: {e}")

    # Second pass: Process and save articles with atomic checks
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_url = {}
        
        for clean_url, article in unique_articles.items():
            # Check MongoDB using URL prefix before processing
            if not collection.find_one({"url": {"$regex": f"^{re.escape(clean_url)}"}}):
                future = executor.submit(process_and_save_article, article)
                future_to_url[future] = clean_url

        for future in concurrent.futures.as_completed(future_to_url):
            clean_url = future_to_url[future]
            try:
                if future.result():
                    total_articles_saved += 1
            except Exception as e:
                print(f"❌ Failed to save {clean_url}: {e}")

    print(f"🎉 Total new articles saved: {total_articles_saved}")

# === Process and Save Articles ===
def process_and_save_article(article):
    """Process article and save with atomic duplicate prevention"""
    full_text, pub_date, img_urls = get_full_article(article['url'])
    if not full_text:
        return False

    # Create document with original fields only
    doc = {
        "title": article['title'],
        "url": article['url'],
        "content": full_text,
        "date": pub_date,
        "images": img_urls
    }

    # Atomic insert-if-not-exists using URL prefix
    try:
        result = collection.update_one(
            {"url": {"$regex": f"^{re.escape(article['url'].split('?')[0])}"}},
            {"$setOnInsert": doc},
            upsert=True
        )
        return result.upserted_id is not None
    except Exception as e:
        print(f"❌ Database error for {article['url']}: {e}")
        return False
    
# Run the scraper
scrape_all_sections()



