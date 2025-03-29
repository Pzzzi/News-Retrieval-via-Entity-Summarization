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

# === Load Summarization Pipeline ===
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# === Fetch Article Summary ===
def get_article_summary(article_id):
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
        return {"summary": summary}
    
    except Exception as e:
        print(f"Error fetching article summary: {e}")
        return {"error": "Internal Server Error"}

