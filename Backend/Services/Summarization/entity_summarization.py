import os
import threading
from transformers import pipeline
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import torch
import logging
from functools import wraps
import gc

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
MONGO_URI = os.getenv("MONGO_URI")
MODEL_NAME = "sshleifer/distilbart-cnn-12-6"
MAX_INPUT_LENGTH = 1024
SUMMARY_MAX_LENGTH = 130
SUMMARY_MIN_LENGTH = 30
FALLBACK_MODEL = "facebook/bart-large-cnn"
ENTITY_SUMMARY_LENGTH = 100

# Global model instance with better management
summarizer_instance = None
model_lock = threading.Lock()

def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return {"error": "Service temporarily unavailable"}, 503
    return wrapper

def initialize_services():
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()
        db = mongo_client["news_db"]
        collection = db["articles"]
        logger.info("MongoDB connection established")
        return collection
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise RuntimeError("Database service unavailable")

collection = initialize_services()

def get_device():
    try:
        if torch.cuda.is_available():
            return torch.device("cuda:0")
        return torch.device("cpu")
    except Exception as e:
        logger.warning(f"Device detection failed, defaulting to CPU: {e}")
        return torch.device("cpu")

def cleanup_model():
    global summarizer_instance
    if summarizer_instance is not None:
        try:
            if hasattr(summarizer_instance, 'model'):
                del summarizer_instance.model
            if hasattr(summarizer_instance, 'tokenizer'):
                del summarizer_instance.tokenizer
            del summarizer_instance
            summarizer_instance = None
        except Exception as e:
            logger.warning(f"Model cleanup failed: {e}")
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

def load_summarizer_at_startup():
    """Called once during backend service startup"""
    global summarizer_instance
    with model_lock:
        if summarizer_instance is not None:
            return

        device = get_device()
        model_to_load = MODEL_NAME

        try:
            cleanup_model()
            logger.info(f"Loading model {model_to_load} on {device}")
            summarizer_instance = pipeline(
                "summarization",
                model=model_to_load,
                device=0 if device.type == "cuda" else -1,
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                truncation=True
            )
            summarizer_instance("Warmup input text.", max_length=10, min_length=5)
            logger.info(f"Successfully loaded model {model_to_load}")
        except Exception as e:
            logger.error(f"Primary model load failed: {e}")
            cleanup_model()
            if model_to_load != FALLBACK_MODEL:
                try:
                    logger.info(f"Loading fallback model {FALLBACK_MODEL} on CPU")
                    summarizer_instance = pipeline(
                        "summarization",
                        model=FALLBACK_MODEL,
                        device=-1,
                        truncation=True
                    )
                    summarizer_instance("Warmup input text.", max_length=10, min_length=5)
                    logger.info(f"Fallback model loaded")
                except Exception as fallback_error:
                    logger.error(f"Fallback model load failed: {fallback_error}")
                    summarizer_instance = None
                    raise RuntimeError("Failed to load summarization models")

# Load the model at startup
load_summarizer_at_startup()

def preprocess_content(content):
    if not content or not isinstance(content, str):
        return ""
    try:
        return " ".join(content.split())[:MAX_INPUT_LENGTH]
    except Exception as e:
        logger.error(f"Content preprocessing failed: {e}")
        return ""

def chunked_summarize(content, chunk_size=512, max_length=SUMMARY_MAX_LENGTH, min_length=SUMMARY_MIN_LENGTH):
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    summaries = []

    for chunk in chunks:
        try:
            result = summarizer_instance(
                chunk,
                max_length=min(max_length, len(chunk)//2),
                min_length=min(min_length, len(chunk)//4),
                do_sample=False
            )
            summaries.append(result[0]["summary_text"])
        except Exception as e:
            logger.warning(f"Chunk summarization failed, fallback used: {e}")
            summaries.append(chunk[:50] + "...")
    return " ".join(summaries)

@handle_errors
def get_article_summary(article_id):
    try:
        obj_id = ObjectId(article_id)
    except Exception:
        return {"error": "Invalid article ID format"}, 400

    try:
        article = collection.find_one({"_id": obj_id})
        if not article:
            return {"error": "Article not found"}, 404
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {"error": "Database operation failed"}, 500

    content = preprocess_content(article.get("content", ""))
    if not content:
        return {"error": "No valid content available to summarize"}, 400

    try:
        if len(content) > 512:
            summary = chunked_summarize(content)
        else:
            result = summarizer_instance(
                content,
                max_length=SUMMARY_MAX_LENGTH,
                min_length=SUMMARY_MIN_LENGTH,
                do_sample=False
            )
            summary = result[0]["summary_text"]
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        summary = content[:100] + "..."

    response = {
        "article_id": str(article.get("_id", "")),
        "article_title": article.get("title", "Untitled Article"),
        "article_url": article.get("url", "#"),
        "summary": summary,
        "date": article.get("date", ""),
        "images": article.get("images", []),
        "entities": []
    }

    try:
        if "entities" in article:
            response["entities"] = [{
                "label": entity.get("label", entity.get("text", "")),
                "type": entity.get("type", ""),
                "description": entity.get("description", ""),
                "wikidata_url": entity.get("wikidata_url", "")
            } for entity in article["entities"] if isinstance(entity, dict)]
    except Exception as e:
        logger.error(f"Entity processing failed: {e}")
        response["entities"] = []

    return response

@handle_errors
def get_entity_summary(entity_name):
    if not entity_name or not isinstance(entity_name, str) or len(entity_name.strip()) < 2:
        return {"error": "Invalid entity name"}, 400

    try:
        articles = list(collection.find({
            "$or": [
                {"entities.text": {"$regex": f"^{entity_name}$", "$options": "i"}},
                {"entities.label": {"$regex": f"^{entity_name}$", "$options": "i"}}
            ]
        }).limit(50))
    except Exception as e:
        logger.error(f"Entity query failed: {e}")
        return {"error": "Database operation failed"}, 500

    if not articles:
        return {"error": "No articles found for this entity"}, 404

    titles = [str(article["title"]) for article in articles if "title" in article]

    if not titles:
        return {"error": "No valid titles found for this entity"}, 404

    combined_text = preprocess_content(" ".join(titles))

    try:
        if len(combined_text) > 512:
            summary = chunked_summarize(
                combined_text,
                max_length=ENTITY_SUMMARY_LENGTH,
                min_length=ENTITY_SUMMARY_LENGTH // 3
            )
        else:
            result = summarizer_instance(
                combined_text,
                max_length=ENTITY_SUMMARY_LENGTH,
                min_length=ENTITY_SUMMARY_LENGTH // 3,
                do_sample=False
            )
            summary = result[0]["summary_text"]
    except Exception as e:
        logger.error(f"Entity summarization failed: {e}")
        summary = ". ".join(titles[:3]) + "..." if len(titles) > 3 else ". ".join(titles)

    return {
        "summary": summary,
        "entity_name": entity_name,
        "source": "titles",
        "article_count": len(articles),
        "warning": "Summary may be approximate" if "..." in summary else None
    }

