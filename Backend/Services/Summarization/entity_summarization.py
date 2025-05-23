import os
from transformers import pipeline
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import torch
import logging
from functools import wraps

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

# Global model instance with lazy loading
summarizer_instance = None
model_loaded = False
load_attempts = 0
MAX_LOAD_ATTEMPTS = 2

def handle_errors(func):
    """Decorator for comprehensive error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return {"error": "Service temporarily unavailable"}, 503
    return wrapper

def initialize_services():
    """Initialize MongoDB connection with error handling"""
    try:
        mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        mongo_client.server_info()  # Test connection
        db = mongo_client["news_db"]
        collection = db["test_articles"]
        logger.info("MongoDB connection established")
        return collection
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {e}")
        raise RuntimeError("Database service unavailable")

collection = initialize_services()

def get_device():
    """Determine the best available device with fallback"""
    try:
        if torch.cuda.is_available():
            return 0  # Use first GPU
        return -1  # Use CPU
    except Exception as e:
        logger.warning(f"Device detection failed, defaulting to CPU: {e}")
        return -1

def load_summarizer():
    """Lazy loading of summarization model with fallbacks"""
    global summarizer_instance, model_loaded, load_attempts
    
    if model_loaded:
        return summarizer_instance
    
    if load_attempts >= MAX_LOAD_ATTEMPTS:
        logger.error("Max model load attempts reached")
        raise RuntimeError("Model loading failed after multiple attempts")
    
    device = get_device()
    model_to_load = MODEL_NAME if load_attempts == 0 else FALLBACK_MODEL
    
    try:
        logger.info(f"Attempting to load model {model_to_load} on device {device} (attempt {load_attempts + 1})")
        
        # Clear GPU cache if available
        if device >= 0:
            torch.cuda.empty_cache()
        
        summarizer_instance = pipeline(
            "summarization",
            model=model_to_load,
            device=device,
            truncation=True,
            torch_dtype=torch.float16 if device >= 0 else torch.float32
        )
        
        model_loaded = True
        logger.info(f"Successfully loaded {model_to_load}")
        return summarizer_instance
    
    except Exception as e:
        load_attempts += 1
        logger.error(f"Model load failed (attempt {load_attempts}): {e}")
        
        # Try again with CPU if GPU failed
        if device >= 0:
            logger.info("Retrying with CPU...")
            return load_summarizer()
        
        raise

def preprocess_content(content):
    """Clean and prepare content for summarization with validation"""
    if not content or not isinstance(content, str):
        return ""
    
    try:
        # Basic cleaning
        content = " ".join(content.split())
        return content[:MAX_INPUT_LENGTH]
    except Exception as e:
        logger.error(f"Content preprocessing failed: {e}")
        return ""

@handle_errors
def get_article_summary(article_id):
    """Generate article summary with comprehensive error handling"""
    # Validate article ID
    try:
        obj_id = ObjectId(article_id)
    except Exception as e:
        logger.error(f"Invalid article ID format: {article_id}")
        return {"error": "Invalid article ID format"}, 400

    # Fetch article with error handling
    try:
        article = collection.find_one({"_id": obj_id})
        if not article:
            return {"error": "Article not found"}, 404
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return {"error": "Database operation failed"}, 500

    # Get and preprocess content
    content = preprocess_content(article.get("content", ""))
    if not content:
        return {"error": "No valid content available to summarize"}, 400

    # Attempt to get summary
    try:
        summarizer = load_summarizer()
        summary_result = summarizer(
            content,
            max_length=SUMMARY_MAX_LENGTH,
            min_length=SUMMARY_MIN_LENGTH,
            do_sample=False
        )
        summary = summary_result[0]["summary_text"]
    except RuntimeError as e:
        if "CUDA out of memory" in str(e):
            logger.warning("CUDA OOM error, retrying with batch processing")
            try:
                # Try processing in smaller chunks
                chunk_size = len(content) // 2
                summary_parts = []
                for i in range(0, len(content), chunk_size):
                    chunk = content[i:i + chunk_size]
                    part = summarizer(
                        chunk,
                        max_length=SUMMARY_MAX_LENGTH // 2,
                        min_length=SUMMARY_MIN_LENGTH // 2,
                        do_sample=False
                    )[0]["summary_text"]
                    summary_parts.append(part)
                summary = " ".join(summary_parts)
            except Exception as inner_e:
                logger.error(f"Chunked processing failed: {inner_e}")
                summary = content[:100] + "..."  # Fallback to truncation
        else:
            logger.error(f"Summarization failed: {e}")
            summary = content[:100] + "..."  # Basic fallback

    except Exception as e:
        logger.error(f"Unexpected summarization error: {e}")
        summary = content[:100] + "..."  # Basic fallback

    # Prepare response with fallback values for all fields
    response = {
        "article_id": str(article.get("_id", "")),
        "article_title": article.get("title", "Untitled Article"),
        "article_url": article.get("url", "#"),
        "summary": summary,
        "date": article.get("date", ""),
        "images": article.get("images", []),
        "entities": []
    }

    # Safely process entities
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
    """Generate entity summary with comprehensive error handling"""
    if not entity_name or not isinstance(entity_name, str) or len(entity_name.strip()) < 2:
        return {"error": "Invalid entity name"}, 400

    try:
        # Case-insensitive search with safe fallback
        articles = list(collection.find({
            "$or": [
                {"entities.text": {"$regex": f"^{entity_name}$", "$options": "i"}},
                {"entities.label": {"$regex": f"^{entity_name}$", "$options": "i"}}
            ]
        }).limit(50))  # Safe limit
    except Exception as e:
        logger.error(f"Entity query failed: {e}")
        return {"error": "Database operation failed"}, 500

    if not articles:
        return {"error": "No articles found for this entity"}, 404

    # Extract and clean titles safely
    titles = []
    for article in articles:
        try:
            if isinstance(article, dict) and "title" in article:
                titles.append(str(article["title"]))
        except Exception as e:
            logger.warning(f"Failed to process article title: {e}")

    if not titles:
        return {"error": "No valid titles found for this entity"}, 404

    combined_text = " ".join(titles)
    combined_text = preprocess_content(combined_text)

    # Attempt summarization
    try:
        summarizer = load_summarizer()
        summary_result = summarizer(
            combined_text,
            max_length=100,
            min_length=30,
            do_sample=False
        )
        summary = summary_result[0]["summary_text"]
    except Exception as e:
        logger.error(f"Entity summarization failed: {e}")
        # Fallback to simple concatenation
        summary = ". ".join(titles[:3]) + "..." if len(titles) > 3 else ". ".join(titles)

    return {
        "summary": summary,
        "entity_name": entity_name,
        "source": "titles",
        "article_count": len(articles),
        "warning": "Summary may be approximate" if "..." in summary else None
    }
