import os
from transformers import pipeline
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["articles"]

# Load summarization pipeline
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def get_article_summary(article_id):
    """Fetch and generate article summary only"""
    try:
        article = collection.find_one({"_id": ObjectId(article_id)})
        if not article:
            return {"error": "Article not found"}

        content = article.get("content", "")
        if not content:
            return {"error": "No content to summarize"}

        # Generate summary (limit BART input to 1024 tokens)
        max_input = 1024
        content = content[:max_input]
        
        summary = summarizer(content, max_length=130, min_length=30, do_sample=False)[0]["summary_text"]
        return {
            "summary": summary,
            "article_title": article["title"],  # Include title for context
            "article_url": article["url"]       # Include URL for reference
        }
    
    except Exception as e:
        print(f"Error fetching article summary: {e}")
        return {"error": "Internal Server Error"}

def get_entity_summary(entity_name):
    """Generate a summary for an entity using article titles only."""
    try:
        articles = collection.find({
            "entities.text": {
                "$regex": f"^{entity_name}$",
                "$options": "i"
            }
        })

        titles = [article.get("title", "") for article in articles if article.get("title")]

        if not titles:
            return {"error": "No titles found for the given entity"}

        combined_titles = " ".join(titles)

        summary = summarizer(
            combined_titles[:1024],
            max_length=100,
            min_length=30,
            do_sample=False
        )[0]["summary_text"]

        return {
            "summary": summary,
            "entity_name": entity_name,
            "source": "titles"
        }

    except Exception as e:
        print(f"Error generating summary from titles: {e}")
        return {"error": "Internal Server Error"}


