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
            return torch.device("cuda:0")
        return torch.device("cpu")
    except Exception as e:
        logger.warning(f"Device detection failed, defaulting to CPU: {e}")
        return torch.device("cpu")

def cleanup_model():
    """Clean up model resources"""
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

def load_summarizer():
    """Thread-safe lazy loading of summarization model with better resource management"""
    global summarizer_instance
    
    with model_lock:
        if summarizer_instance is not None:
            return summarizer_instance
        
        device = get_device()
        model_to_load = MODEL_NAME
        
        try:
            logger.info(f"Loading model {model_to_load} on {device}")
            
            # Clear resources before loading
            cleanup_model()
            
            summarizer_instance = pipeline(
                "summarization",
                model=model_to_load,
                device=device,
                truncation=True,
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32
            )
            
            # Warm up the model
            try:
                summarizer_instance("This is a warmup sentence.", max_length=10, min_length=5)
            except Exception as warmup_error:
                logger.warning(f"Model warmup failed: {warmup_error}")
            
            logger.info(f"Successfully loaded {model_to_load}")
            return summarizer_instance
        
        except Exception as e:
            logger.error(f"Model load failed: {e}")
            cleanup_model()
            
            # Try fallback model
            if model_to_load != FALLBACK_MODEL:
                logger.info(f"Attempting fallback model {FALLBACK_MODEL}")
                try:
                    summarizer_instance = pipeline(
                        "summarization",
                        model=FALLBACK_MODEL,
                        device=torch.device("cpu"),  # Force CPU for fallback
                        truncation=True
                    )
                    logger.info(f"Successfully loaded fallback model {FALLBACK_MODEL}")
                    return summarizer_instance
                except Exception as fallback_error:
                    logger.error(f"Fallback model load failed: {fallback_error}")
                    cleanup_model()
            
            raise RuntimeError("Failed to load any summarization model")

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

def chunked_summarize(content, summarizer, chunk_size=512, max_length=SUMMARY_MAX_LENGTH, min_length=SUMMARY_MIN_LENGTH):
    """Process content in chunks to avoid memory issues"""
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    summaries = []
    
    for chunk in chunks:
        try:
            result = summarizer(
                chunk,
                max_length=min(max_length, len(chunk)//2),
                min_length=min(min_length, len(chunk)//4),
                do_sample=False
            )
            summaries.append(result[0]["summary_text"])
        except Exception as e:
            logger.warning(f"Chunk summarization failed, using fallback: {e}")
            summaries.append(chunk[:50] + "...")  # Simple fallback
    
    return " ".join(summaries)

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
        if len(content) > 512:  # Use chunked processing for longer content
            summary = chunked_summarize(content, summarizer)
        else:
            summary_result = summarizer(
                content,
                max_length=SUMMARY_MAX_LENGTH,
                min_length=SUMMARY_MIN_LENGTH,
                do_sample=False
            )
            summary = summary_result[0]["summary_text"]
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.warning("Memory error, retrying with cleanup")
            cleanup_model()
            try:
                summarizer = load_summarizer()
                summary = chunked_summarize(content, summarizer, chunk_size=256)
            except Exception as retry_error:
                logger.error(f"Retry failed: {retry_error}")
                summary = content[:100] + "..."
        else:
            logger.error(f"Summarization failed: {e}")
            summary = content[:100] + "..."
    except Exception as e:
        logger.error(f"Unexpected summarization error: {e}")
        summary = content[:100] + "..."

    # Prepare response
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

    # Attempt summarization with improved error handling
    try:
        summarizer = load_summarizer()
        
        if len(combined_text) > 512:
            summary = chunked_summarize(
                combined_text, 
                summarizer,
                max_length=ENTITY_SUMMARY_LENGTH,
                min_length=ENTITY_SUMMARY_LENGTH//3
            )
        else:
            summary_result = summarizer(
                combined_text,
                max_length=ENTITY_SUMMARY_LENGTH,
                min_length=ENTITY_SUMMARY_LENGTH//3,
                do_sample=False
            )
            summary = summary_result[0]["summary_text"]
            
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.warning("Memory error during entity summarization, retrying with cleanup")
            cleanup_model()
            try:
                summarizer = load_summarizer()
                summary = chunked_summarize(
                    combined_text, 
                    summarizer,
                    chunk_size=256,
                    max_length=ENTITY_SUMMARY_LENGTH,
                    min_length=ENTITY_SUMMARY_LENGTH//3
                )
            except Exception as retry_error:
                logger.error(f"Entity summarization retry failed: {retry_error}")
                summary = ". ".join(titles[:3]) + "..." if len(titles) > 3 else ". ".join(titles)
        else:
            logger.error(f"Entity summarization failed: {e}")
            summary = ". ".join(titles[:3]) + "..." if len(titles) > 3 else ". ".join(titles)
    except Exception as e:
        logger.error(f"Unexpected entity summarization error: {e}")
        summary = ". ".join(titles[:3]) + "..." if len(titles) > 3 else ". ".join(titles)

    return {
        "summary": summary,
        "entity_name": entity_name,
        "source": "titles",
        "article_count": len(articles),
        "warning": "Summary may be approximate" if "..." in summary else None
    }
