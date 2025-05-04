import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
import concurrent.futures
from dotenv import load_dotenv
from dateutil import parser, tz

load_dotenv()

# ====== MongoDB Connection ======
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# ====== The Guardian Section URLs ======
URLS = [
    "https://www.theguardian.com/international",
    "https://www.theguardian.com/world",
    "https://www.theguardian.com/us-news",
    "https://www.theguardian.com/uk-news",
    "https://www.theguardian.com/environment",
    "https://www.theguardian.com/science",
    "https://www.theguardian.com/global-development",
    "https://www.theguardian.com/technology",
    "https://www.theguardian.com/business"
]

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

def normalize_url(url):
    """Remove fragments and query parameters from URL for deduplication"""
    url = url.split('#')[0]  # Remove fragment
    url = url.split('?')[0]  # Remove query parameters
    return url

def scrape_section(url):
    try:
        print(f"🔍 Scraping section: {url}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        out = []
        # Look for article links - they typically contain a date in the path
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Filter for article links (containing /2025/ for current year)
            if (href.startswith("/") and 
                re.match(r"/[a-z-]+/\d{4}/[a-z]{3}/\d{2}/", href)):
                full_url = "https://www.theguardian.com" + href
                out.append({"url": full_url})
        
        print(f"✅ Found {len(out)} articles in {url}")
        return out

    except Exception as e:
        print(f"❌ Error scraping section {url}: {e}")
        return []

def get_full_article(article):
    url = article["url"]
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # --- Title ---
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else None

        # --- Date ---
        pub_date = None
        # Look for date in meta tags first as it's more reliable
        meta_date = soup.find("meta", property="article:published_time")
        if meta_date and meta_date.get("content"):
            dt = parser.parse(meta_date["content"])
            pub_date = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)
        else:
            # Fallback to visible date in the page
            date_tag = soup.find("span", class_=re.compile("dcr-u0h1qy"))
            if date_tag:
                txt = date_tag.get_text(strip=True)
                dt = parser.parse(txt, fuzzy=True)
                pub_date = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)

        # --- Content ---
        article_body = soup.find("div", class_=re.compile("article-body"))
        if not article_body:
            article_body = soup.find("div", id="maincontent")
        
        content = ""
        if article_body:
            paras = article_body.find_all("p", class_=re.compile("dcr-"))
            content = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))

        # --- Images ---
        images = []
        # Get main image from meta tag (with parameters)
        meta_image = soup.find("meta", property="og:image")
        if meta_image and meta_image.get("content"):
            images.append(meta_image["content"])  # Keep full URL with parameters
        
        # Get additional images from picture elements
        for picture in soup.find_all("picture", class_=re.compile("dcr-")):
            sources = picture.find_all("source")
            for source in sources:
                if source.get("srcset"):
                    # Extract all URLs from srcset and take the first complete URL
                    srcset = source["srcset"]
                    # Split by commas and take first URL (may include parameters)
                    first_url = srcset.split(',')[0].split()[0]
                    if first_url.startswith("https://"):
                        images.append(first_url)
                        break  # Only need one URL per picture element

        # Skip if essential data missing
        if not title or not content:
            print(f"⚠️ Skipping (no title/content): {url}")
            return

        doc = {
            "title": title,
            "url": url,
            "content": content,
            "date": pub_date,
            "images": list(set(images)),  # Remove duplicates
        }

        # Normalize URL for deduplication
        clean_url = normalize_url(url)
        res = collection.update_one(
            {"url": {"$regex": f"^{re.escape(clean_url)}(#|\?|$)"}},
            {"$setOnInsert": doc},
            upsert=True
        )
        if res.upserted_id:
            print(f"✅ Saved: {title[:60]}...")
            return True
        return False

    except Exception as e:
        print(f"❌ Error processing article {url}: {e}")
        return False

def scrape_all_sections():
    seen = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as exec1:
        all_lists = exec1.map(scrape_section, URLS)
        all_articles = [item for sub in all_lists for item in sub]

    if not all_articles:
        print("⚠️ No articles found!")
        return

    # Deduplicate using normalized URLs
    unique = []
    for art in all_articles:
        clean = normalize_url(art["url"])
        if clean not in seen:
            seen.add(clean)
            unique.append(art)
    
    print(f"🔎 Total unique articles to process: {len(unique)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exec2:
        results = list(exec2.map(get_full_article, unique))

    saved_count = sum(1 for r in results if r)
    print(f"✅ Scraping finished. Articles saved: {saved_count} / {len(unique)}")
    print("🎉 The Guardian scraping complete.")

if __name__ == "__main__":
    scrape_all_sections()