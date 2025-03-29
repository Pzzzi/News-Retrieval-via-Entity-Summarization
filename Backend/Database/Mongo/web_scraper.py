import requests
import os 
from bs4 import BeautifulSoup
from pymongo import MongoClient
import concurrent.futures  # For parallel requests
import time
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URI=os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# BBC News URLs
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

# Function to extract full article text
def get_full_article(article_url):
    try:
        response = requests.get(article_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            article_tag = soup.find("article")

            if not article_tag:
                return None

            paragraphs = article_tag.find_all("p")
            full_text = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
            return full_text if full_text else None
        return None
    except Exception as e:
        print(f"❌ Error fetching article {article_url}: {e}")
        return None

# Function to scrape a single section
def scrape_section(url):
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

# Function to scrape all sections in parallel
def scrape_all_sections():
    total_articles_saved = 0
    all_articles = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(scrape_section, URLS)
        for section_articles in results:
            all_articles.extend(section_articles)

    # Fetch full article text in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for article, full_text in zip(all_articles, executor.map(get_full_article, [a["url"] for a in all_articles])):
            if full_text:
                article["content"] = full_text
                collection.insert_one(article)  # Insert into MongoDB
                total_articles_saved += 1
                print(f"✅ Saved: {article['title']}")

    print(f"🎉 Total new articles saved: {total_articles_saved}")

# Run the scraper
scrape_all_sections()
