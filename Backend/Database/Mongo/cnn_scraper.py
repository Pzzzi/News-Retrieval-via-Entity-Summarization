import os
import re
import threading
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
client     = MongoClient(MONGO_URI)
db         = client["news_db"]
collection = db["articles"]

# ====== CNN URLs ======
URLS = [
    "https://edition.cnn.com/",
    "https://edition.cnn.com/world",
    "https://edition.cnn.com/politics",
    "https://edition.cnn.com/business",
    "https://edition.cnn.com/world",
    "https://edition.cnn.com/health",
    "https://edition.cnn.com/entertainment",
    "https://edition.cnn.com/style",
    "https://edition.cnn.com/travel",
    "https://edition.cnn.com/science",
    "https://edition.cnn.com/climate",
    "https://edition.cnn.com/weather",
]

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
}

def scrape_section(url):
    """Phase 1: Just collect url pairs."""
    try:
        print(f"🔍 Scraping section: {url}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        out = []
        for a in soup.find_all("a", href=True, attrs={"data-link-type": "article"}):
            href = a["href"]
            if href.startswith("/"):
                href = "https://edition.cnn.com" + href
            out.append({"url": href})
        print(f"✅ Found {len(out)} articles in {url}")
        return out

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return []

def get_full_article(article):
    """Phase 2 worker: fetch content, date, images, and insert to Mongo."""
    url = article["url"]

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # --- TITLE EXTRACTION (strict) ---
        # 1) Try H1 with id="maincontent"
        h1 = soup.find("h1", id="maincontent")
        if h1 and h1.text.strip():
            title = h1.text.strip()
        else:
            # 2) Fallback to Open Graph <meta> tag
            og = soup.find("meta", property="og:title")
            title = og["content"].strip() if og and og.get("content") else None

        # --- DATE with conversion to Asia/Kuala_Lumpur ---
        date_tag = soup.find("div", class_=re.compile("timestamp"))
        pub_date = None
        if date_tag:
            txt = date_tag.get_text(strip=True).replace("Updated", "").strip()
            dt  = parser.parse(txt, fuzzy=True)
            dt_kl = dt.astimezone(tz.gettz("Asia/Kuala_Lumpur")).replace(tzinfo=None)
            pub_date = dt_kl

        # --- CONTENT ---
        paras = soup.find_all("p", class_=re.compile("paragraph"))
        content = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))

        # --- IMAGES ---
        images = []
        for pic in soup.find_all("picture"):
            for src in pic.find_all("source", srcset=True):
                images.append(src["srcset"])

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

        # atomic upsert
        clean = re.escape(url.split("?")[0])
        res = collection.update_one(
            {"url": {"$regex": f"^{clean}"}},
            {"$setOnInsert": doc},
            upsert=True
        )
        if res.upserted_id:
            print(f"✅ Saved: {title[:50]}...")

    except Exception as e:
        print(f"❌ Error processing {url}: {e}")

def scrape_all_sections():
    """Orchestrate two‐phase parallel scrape & ingest."""
    seen = set()

    # Phase 1: collect URLs
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as exec1:
        all_lists = exec1.map(scrape_section, URLS)
        all_articles = [item for sub in all_lists for item in sub]

    if not all_articles:
        print("⚠️ No articles found at all!")
        return

    # Deduplicate URLs
    unique = []
    for art in all_articles:
        clean = art["url"].split("?")[0]
        if clean not in seen:
            seen.add(clean)
            unique.append(art)

    # Phase 2: fetch & insert
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exec2:
        exec2.map(get_full_article, unique)

    total = collection.count_documents({"url": {"$regex": "^https://edition.cnn.com"}})
    print(f"🗞️ Total CNN articles in MongoDB: {total}")
    print("🎉 CNN scraping complete.")

if __name__ == "__main__":
    scrape_all_sections()



