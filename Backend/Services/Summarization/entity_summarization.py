import os
from transformers import pipeline
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import torch
import logging
from functools import lru_cache

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["test_articles"]

# Configure model settings
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
DEVICE = 0 if torch.cuda.is_available() else -1
MAX_INPUT_LENGTH = 1024
SUMMARY_MAX_LENGTH = 130
SUMMARY_MIN_LENGTH = 30

@lru_cache(maxsize=1)
def get_summarizer():
    """Cache the summarizer model to avoid repeated loading"""
    try:
        logger.info(f"Loading summarization model {MODEL_NAME} on device {DEVICE}...")
        summarizer = pipeline(
            "summarization",
            model=MODEL_NAME,
            device=DEVICE,
            truncation=True
        )
        logger.info("Summarization model loaded successfully")
        return summarizer
    except Exception as e:
        logger.error(f"Failed to load summarization model: {e}")
        raise

def preprocess_content(content):
    """Clean and prepare content for summarization"""
    if not content:
        return ""
    
    # Basic cleaning - remove excessive whitespace and newlines
    content = " ".join(content.split())
    return content[:MAX_INPUT_LENGTH]

def get_article_summary(article_id):
    """Fetch and generate article summary with robust error handling"""
    try:
        # Validate article ID
        try:
            obj_id = ObjectId(article_id)
        except:
            return {"error": "Invalid article ID format"}, 400

        # Fetch article
        article = collection.find_one({"_id": obj_id})
        if not article:
            return {"error": "Article not found"}, 404

        # Get and preprocess content
        content = preprocess_content(article.get("content"))
        if not content:
            return {"error": "No content available to summarize"}, 400

        try:
            # Generate summary
            summarizer = get_summarizer()
            summary = summarizer(
                content,
                max_length=SUMMARY_MAX_LENGTH,
                min_length=SUMMARY_MIN_LENGTH,
                do_sample=False
            )[0]["summary_text"]
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                logger.warning("CUDA OOM error, retrying with CPU")
                torch.cuda.empty_cache()
                summarizer.device = -1  # Fall back to CPU
                summary = summarizer(
                    content,
                    max_length=SUMMARY_MAX_LENGTH,
                    min_length=SUMMARY_MIN_LENGTH,
                    do_sample=False
                )[0]["summary_text"]
            else:
                raise

        return {
            "summary": summary,
            "article_title": article.get("title", "Untitled Article"),
            "article_url": article.get("url", "#"),
            "article_id": str(article["_id"])
        }

    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        return {"error": "Internal server error during summarization"}, 500

def get_entity_summary(entity_name):
    """Generate a summary for an entity using article titles"""
    try:
        if not entity_name or len(entity_name.strip()) < 2:
            return {"error": "Entity name too short"}, 400

        # Case-insensitive exact match search
        articles = list(collection.find({
            "$or": [
                {"entities.text": {"$regex": f"^{entity_name}$", "$options": "i"}},
                {"entities.label": {"$regex": f"^{entity_name}$", "$options": "i"}}
            ]
        }).limit(50))  # Limit to prevent excessive memory usage

        if not articles:
            return {"error": "No articles found for this entity"}, 404

        # Extract and clean titles
        titles = [a.get("title", "") for a in articles if a.get("title")]
        if not titles:
            return {"error": "No valid titles found for this entity"}, 404

        # Combine titles and preprocess
        combined_text = " ".join(titles)
        combined_text = preprocess_content(combined_text)

        try:
            # Generate summary
            summarizer = get_summarizer()
            summary = summarizer(
                combined_text,
                max_length=100,
                min_length=30,
                do_sample=False
            )[0]["summary_text"]
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                logger.warning("CUDA OOM error, retrying with CPU")
                torch.cuda.empty_cache()
                summarizer.device = -1  # Fall back to CPU
                summary = summarizer(
                    combined_text,
                    max_length=100,
                    min_length=30,
                    do_sample=False
                )[0]["summary_text"]
            else:
                raise

        return {
            "summary": summary,
            "entity_name": entity_name,
            "source": "titles",
            "article_count": len(articles)
        }

    except Exception as e:
        logger.error(f"Error generating entity summary: {e}")
        return {"error": "Internal server error during entity summarization"}, 500
