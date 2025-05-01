import os
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
import concurrent.futures
from dotenv import load_dotenv
from dateutil import parser, tz
from urllib.parse import unquote

load_dotenv()

# ====== MongoDB Connection ======
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# ====== AP News Section URLs ======
URLS = [
    "https://apnews.com/",
    "https://apnews.com/world-news",
    "https://apnews.com/us-news",
    "https://apnews.com/politics",
    "https://apnews.com/sports",
    "https://apnews.com/entertainment",
    "https://apnews.com/business",
    "https://apnews.com/science",
    "https://apnews.com/health",
    "https://apnews.com/technology",
    "https://apnews.com/lifestyle",
    "https://apnews.com/climate-and-environment"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def scrape_section(url):
    try:
        print(f"🔍 Scraping section: {url}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        out = []
        # Find all article links - look for <a> tags with article URLs
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Match article URLs pattern
            if re.match(r'^https://apnews.com/article/[\w-]+$', href):
                out.append({"url": href})
        
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
        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else None

        # --- Date --- (More robust extraction)
        pub_date = None
        # Method 1: Extract from bsp-timestamp data attribute
        timestamp_tag = soup.find("bsp-timestamp", attrs={"data-timestamp": True})
        if timestamp_tag:
            try:
                timestamp = int(timestamp_tag["data-timestamp"]) / 1000  # Convert to seconds
                dt = datetime.fromtimestamp(timestamp, tz=tz.gettz("Asia/Kuala_Lumpur"))
                pub_date = dt.replace(tzinfo=None)
            except Exception as e:
                print(f"⚠️ Couldn't parse timestamp: {e}")

        # Method 2: Extract from visible date text
        if not pub_date:
            date_span = soup.find("span", attrs={"data-date": True})
            if date_span:
                date_text = date_span.get_text(strip=True)
                # Clean the date string
                date_text = re.sub(r'^Updated\s*', '', date_text)
                try:
                    dt = parser.parse(date_text, fuzzy=True)
                    pub_date = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)
                except Exception as e:
                    print(f"⚠️ Couldn't parse date text: {e}")

        # --- Content --- (Filter out copyright notices)
        content = ""
        body = soup.find("div", class_=re.compile("RichTextStoryBody|article-body"))
        if body:
            paras = body.find_all("p")
            content_paras = []
            for p in paras:
                text = p.get_text(strip=True)
                # Skip copyright notices and short paragraphs
                if (not text.startswith("Copyright") and 
                    not text.startswith("AP ") and 
                    len(text.split()) > 5):
                    content_paras.append(text)
            content = "\n".join(content_paras)

        # --- Images --- (Extract original URLs from dims.apnews.com links)
        images = []
        
        # 1. Get the main featured image from meta tags
        for meta in soup.find_all("meta", property=["og:image", "twitter:image"]):
            img_url = meta.get("content", "")
            if img_url:
                # Extract original URL from dims.apnews.com links
                if "dims.apnews.com" in img_url and "url=" in img_url:
                    match = re.search(r'url=([^&]+)', img_url)
                    if match:
                        original_url = unquote(match.group(1))
                        if original_url.startswith(('http://', 'https://')):
                            images.append(original_url)
                else:
                    # Regular image URL
                    images.append(img_url.split('?')[0])
        
        # 2. Get images from article body
        article_body = soup.find("div", class_=re.compile("RichTextStoryBody|article-body"))
        if article_body:
            # Find all image containers
            for img_container in article_body.find_all(["figure", "div", "picture"]):
                # Check for picture > source elements
                picture = img_container.find("picture")
                if picture:
                    for source in picture.find_all("source", srcset=True):
                        # Process each URL in srcset
                        for src in source["srcset"].split(','):
                            img_url = src.strip().split()[0]
                            if "dims.apnews.com" in img_url and "url=" in img_url:
                                match = re.search(r'url=([^&]+)', img_url)
                                if match:
                                    original_url = unquote(match.group(1))
                                    if original_url.startswith(('http://', 'https://')):
                                        images.append(original_url)
                            elif "apnews.com" in img_url:
                                images.append(img_url.split('?')[0])
                
                # Check for regular img tags
                img = img_container.find("img", src=True)
                if img:
                    img_url = img.get("src") or img.get("data-src", "")
                    if "dims.apnews.com" in img_url and "url=" in img_url:
                        match = re.search(r'url=([^&]+)', img_url)
                        if match:
                            original_url = unquote(match.group(1))
                            if original_url.startswith(('http://', 'https://')):
                                images.append(original_url)
                    elif "apnews.com" in img_url:
                        images.append(img_url.split('?')[0])

        # Filter out unwanted images and duplicates
        final_images = []
        seen_images = set()
        for img in images:
            # Skip assets, logos, and placeholders
            if not any(x in img.lower() for x in ["/assets/", "/logo", "/promo", "placeholder"]):
                clean_url = img.split('#')[0]  # Remove fragments
                if clean_url not in seen_images:
                    seen_images.add(clean_url)
                    final_images.append(clean_url)

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

        clean_url = url.split('?')[0].split('#')[0]
        res = collection.update_one(
            {"url": {"$regex": f"^{re.escape(clean_url)}(#|\?|$)"}},
            {"$setOnInsert": doc},
            upsert=True
        )
        if res.upserted_id:
            print(f"✅ Saved: {title[:60]}...")

    except Exception as e:
        print(f"❌ Error processing article {url}: {e}")

def scrape_all_sections():
    seen = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as exec1:
        all_lists = exec1.map(scrape_section, URLS)
        all_articles = [item for sub in all_lists for item in sub]

    if not all_articles:
        print("⚠️ No articles found! Trying alternative scraping method...")
        # Fallback method - try to find links by URL pattern only
        try:
            r = requests.get("https://apnews.com/", headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            all_articles = [{"url": a["href"]} for a in soup.find_all("a", href=True) 
                           if re.match(r'^https://apnews.com/article/[\w-]+$', a["href"])]
            print(f"Found {len(all_articles)} articles with fallback method")
        except Exception as e:
            print(f"❌ Fallback method failed: {e}")
            return

    # Deduplicate
    unique = []
    for art in all_articles:
        clean = art["url"].split('?')[0].split('#')[0]
        if clean not in seen:
            seen.add(clean)
            unique.append(art)
    
    print(f"🔎 Total unique articles to process: {len(unique)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exec2:
        exec2.map(get_full_article, unique)

    print(f"✅ Scraping finished. Total articles scraped: {len(unique)}")
    print("🎉 AP News scraping complete.")

if __name__ == "__main__":
    scrape_all_sections()