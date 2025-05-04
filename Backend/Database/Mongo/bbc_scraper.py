import os
import re
import threading
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from pymongo import MongoClient
import concurrent.futures
from dotenv import load_dotenv
from dateutil import parser

load_dotenv()

# ====== MongoDB Connection ======
MONGO_URI  = os.getenv("MONGO_URI")
client     = MongoClient(MONGO_URI)
db         = client["news_db"]
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
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

def scrape_section(url):
    """Phase 1: gather all article URLs from a section."""
    try:
        print(f"🔍 Scraping section: {url}")
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        out = []
        for a in soup.find_all("a", href=True):
            # BBC index pages wrap headlines in <h3> or <h2>
            if a.find("h3") or a.find("h2"):
                href = a["href"]
                if href.startswith("/"):
                    href = "https://www.bbc.com" + href
                out.append({"url": href})
        print(f"✅ Found {len(out)} articles in {url}")
        return out

    except Exception as e:
        print(f"❌ Error scraping {url}: {e}")
        return []

def get_full_article(article):
    """Phase 2: fetch each article page & upsert into Mongo."""
    url = article["url"]

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # --- TITLE ---
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 and h1.text.strip() else None

        # --- DATE ---
        time_tag = soup.find("time")
        pub_date = None
        if time_tag and time_tag.has_attr("datetime"):
            try:
                dt = parser.parse(time_tag["datetime"])
                pub_date = dt
            except Exception:
                pub_date = None

        # --- CONTENT ---
        article_tag = soup.find("article")
        paras = article_tag.find_all("p") if article_tag else []
        content = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True))

        # --- IMAGES ---
        img_urls = set()
        if article_tag:
            for img in article_tag.find_all("img"):
                src = img.get("src") or ""
                if src.startswith("http"):
                    img_urls.add(src)
                for candidate in img.get("srcset", "").split(","):
                    url_part = candidate.strip().split(" ")[0]
                    if url_part.startswith("http"):
                        img_urls.add(url_part)

        if not title or not content:
            print(f"⚠️ Skipping (no title/content): {url}")
            return False

        doc = {
            "title":   title,
            "url":     url,
            "content": content,
            "date":    pub_date,
            "images":  list(img_urls)
        }

        clean = re.escape(url.split("?")[0].rstrip("/"))
        res = collection.update_one(
            {"url": {"$regex": f"^{clean}$"}},
            {"$setOnInsert": doc},
            upsert=True
        )
        if res.upserted_id:
            print(f"✅ Saved: {title[:50]}…")
            return True
        return False

    except Exception as e:
        print(f"❌ Error processing {url}: {e}")
        return False

def scrape_all_sections():
    """Orchestrate two‐phase parallel scrape & ingest for BBC."""
    seen = set()

    # Phase 1: gather URLs in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as exec1:
        all_lists    = exec1.map(scrape_section, URLS)
        all_articles = [item for sub in all_lists for item in sub]

    if not all_articles:
        print("⚠️ No articles found at all!")
        return

    print(f"✅ Total URLs gathered: {len(all_articles)} across {len(URLS)} sections")

    # Deduplicate URLs
    unique = []
    for art in all_articles:
        clean = art["url"].split("?")[0].rstrip("/")
        if clean not in seen:
            seen.add(clean)
            unique.append(art)

    print(f"🔎 Total unique articles to process: {len(unique)}")

    # Phase 2: fetch & insert in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as exec2:
        results = list(exec2.map(get_full_article, unique))

    saved_count = sum(1 for r in results if r)
    print(f"✅ Scraping finished. Articles saved: {saved_count} / {len(unique)}")
    print("🎉 BBC scraping complete.")

if __name__ == "__main__":
    scrape_all_sections()
