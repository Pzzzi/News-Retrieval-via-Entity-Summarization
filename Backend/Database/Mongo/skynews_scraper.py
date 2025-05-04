import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
import concurrent.futures
from dotenv import load_dotenv
from dateutil import parser, tz
from urllib.parse import urljoin

load_dotenv()

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Sky News Section URLs
URLS = [
    "https://news.sky.com/",
    "https://news.sky.com/us",
    "https://news.sky.com/uk",
    "https://news.sky.com/world",
    "https://news.sky.com/money",
    "https://news.sky.com/science-climate-tech",
    "https://news.sky.com/entertainment"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def normalize_url(url):
    """Remove fragments and query parameters from URL for deduplication"""
    return url.split('?')[0].split('#')[0]

def scrape_section(url):
    try:
        print(f"🔍 Scraping section: {url}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        out = []
        base_url = "https://news.sky.com"
        
        # Find article links by URL pattern rather than classes
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Match article URLs (either full URL or path starting with /story/)
            if re.match(r'(^https://news\.sky\.com/story/|^/story/)', href):
                full_url = href if href.startswith('http') else urljoin(base_url, href)
                out.append({"url": normalize_url(full_url)})
        
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

        # Title - look for the first h1 or meta og:title
        title = None
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        else:
            meta_title = soup.find("meta", property="og:title")
            if meta_title:
                title = meta_title.get("content", "").strip()

        # --- Date --- #
        pub_date = None
        # Method 1: Look for datetime attribute in time element
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            try:
                dt = parser.parse(time_tag["datetime"])
                pub_date = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)
            except:
                pass
        
        # Method 2: Look for date text in article header
        if not pub_date:
            header = soup.find(class_=re.compile("article-header"))
            if header:
                date_text = header.find(string=re.compile(r"\b\d{1,2}\s+\w+\s+\d{4}\b"))
                if date_text:
                    try:
                        # Clean Sky News date format (e.g., "Sunday 4 May 2025 04:38, UK")
                        clean_date = re.sub(r",\s*UK$", "", date_text.strip())
                        dt = parser.parse(clean_date, fuzzy=True)
                        pub_date = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)
                    except:
                        pass
        
        if not pub_date:
            # Look for text containing date patterns
            date_pattern = re.compile(r'\b\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b|\b\d{4}-\d{2}-\d{2}\b')
            date_text = soup.find(string=date_pattern)
            if date_text:
                try:
                    dt = parser.parse(date_text, fuzzy=True)
                    pub_date = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)
                except:
                    pass

        # Content - find the main article text
        content = ""
        # Method 1: Look for article body by common attributes
        body = soup.find(attrs={"itemprop": "articleBody"}) or \
               soup.find(role="article") or \
               soup.find("article")
        
        # Method 2: Find the div with the most paragraphs
        if not body:
            body = max(soup.find_all("div"), key=lambda d: len(d.find_all("p")))
        
        if body:
            paras = body.find_all("p")
            content = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))

        # --- Images --- (Filtered to exclude related articles)
        images = []
        # 1. Get main article image from meta
        meta_image = soup.find("meta", property="og:image")
        if meta_image and meta_image.get("content"):
            img_url = meta_image["content"].split('?')[0]
            images.append(img_url)
        
        # 2. Get images from article body (excluding related stories)
        if body:
            # Remove related stories section before finding images
            related = body.find(class_=re.compile("related-stories|related-articles"))
            if related:
                related.decompose()
            
            for img in body.find_all("img", src=True):
                src = img["src"]
                if src.startswith(('http://', 'https://')):
                    clean_src = src.split('?')[0]  # Remove query params
                    if clean_src not in images:
                        images.append(clean_src)

        # Final image filtering
        final_images = [
            img for img in images
            if not any(x in img.lower() for x in ["thumbnail", "related", "promo"])
        ]

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

    # Deduplicate
    unique = []
    for art in all_articles:
        if art["url"] not in seen:
            seen.add(art["url"])
            unique.append(art)
    
    print(f"🔎 Total unique articles to process: {len(unique)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exec2:
        results = list(exec2.map(get_full_article, unique))

    saved_count = sum(1 for r in results if r)
    print(f"✅ Scraping finished. Articles saved: {saved_count} / {len(unique)}")
    print("🎉 Sky News scraping complete.")

if __name__ == "__main__":
    scrape_all_sections()