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

# ====== Al Jazeera Section URLs ======
URLS = [
    "https://www.aljazeera.com/",
    "https://www.aljazeera.com/news/",
    "https://www.aljazeera.com/sports/",
    "https://www.aljazeera.com/opinions/",
    "https://www.aljazeera.com/features/",
    "https://www.aljazeera.com/economy/",
    "https://www.aljazeera.com/climate-crisis",
    "https://www.aljazeera.com/investigations/",
    "https://www.aljazeera.com/tag/human-rights/",
    "https://www.aljazeera.com/tag/science-and-technology/"
]

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

def scrape_section(url):
    try:
        print(f"🔍 Scraping section: {url}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        out = []
        # Look for all <a> tags with proper article href
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Filter for article links only
            if href.startswith("/") and any(href.startswith(p) for p in ["/news/", "/sports/", "/opinions/"]):
                full_url = "https://www.aljazeera.com" + href
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
        date_tag = soup.select_one("div.article-dates div.date-simple span")
        if date_tag and "Published On" in date_tag.text:
            txt = date_tag.text.replace("Published On", "").strip()
            dt = parser.parse(txt, fuzzy=True)
            pub_date = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)

        # --- Content ---
        paras = soup.select("div.wysiwyg p")
        content = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))

        # --- Images ---
        images = []
        for img in soup.select("figure img[src]"):
            src = img.get("src")
            if src and src.startswith("/"):
                src = "https://www.aljazeera.com" + src
            if src:
                images.append(src)

        # Skip if essential data missing
        if not title or not content:
            print(f"⚠️ Skipping (no title/content): {url}")
            return

        doc = {
            "title":   title,
            "url":     url,
            "content": content,
            "date":    pub_date,
            "images":  images
        }

        clean = re.escape(url.split("?")[0])
        res = collection.update_one(
            {"url": {"$regex": f"^{clean}"}},
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
        print("⚠️ No articles found!")
        return

    # Deduplicate
    unique = []
    for art in all_articles:
        clean = art["url"].split("?")[0]
        if clean not in seen:
            seen.add(clean)
            unique.append(art)
    
    print(f"🔎 Total unique articles to process: {len(unique)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exec2:
        exec2.map(get_full_article, unique)

    print(f"✅ Scraping finished. Total articles scraped: {len(unique)}")
    print("🎉 Al Jazeera scraping complete.")

if __name__ == "__main__":
    scrape_all_sections()
