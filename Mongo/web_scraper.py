import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
import time

# MongoDB Connection
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# BBC News URL
URL = "https://www.bbc.com/news"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Function to extract full article text
def get_full_article(article_url):
    """Scrapes the full text of an article from its URL."""
    try:
        response = requests.get(article_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all paragraphs in the article content section
            paragraphs = soup.find_all("p")

            # Combine paragraphs into full text
            full_text = "\n".join([p.text.strip() for p in paragraphs if p.text.strip()])
            return full_text
        else:
            print(f"⚠️ Skipping {article_url}, status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error fetching article {article_url}: {e}")
        return None

# Send GET request to main news page
response = requests.get(URL, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    sections = soup.find_all("section")
    print(f"🔎 Found {len(sections)} sections")

    total_articles = 0  # Counter for saved articles

    for section in sections:
        articles = section.find_all("a", href=True)

        for article in articles:
            title_tag = article.find("h3") or article.find("h2")
            
            if title_tag:
                title = title_tag.text.strip()
                link = f"https://www.bbc.com{article['href']}" if article['href'].startswith("/") else article['href']

                # Check if the article already exists in MongoDB
                if collection.count_documents({"url": link}) == 0:
                    print(f"🌐 Scraping full article: {title}")

                    full_text = get_full_article(link)

                    if full_text:
                        news_item = {
                            "title": title,
                            "url": link,
                            "content": full_text
                        }

                        collection.insert_one(news_item)
                        total_articles += 1
                        print(f"✅ Article saved: {title}")

                    # Sleep to avoid getting blocked
                    time.sleep(2)

    print(f"🎉 Total new articles saved: {total_articles}")

else:
    print(f"❌ Failed to retrieve data: {response.status_code}")
