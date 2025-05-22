import os
from pymongo import MongoClient
from dotenv import load_dotenv
import re

load_dotenv()

# ====== Database Connection ======
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["test_articles"]  # Changed to test_articles

def normalize_entity_name(entity_name):
    """Helper function to normalize entity names for comparison"""
    return entity_name.lower().strip()

def suggest_entities(query):
    """Suggest entities based on search query with normalized labels"""
    if not query or len(query) < 2:
        return {"results": []}  # Single-level response

    normalized_query = normalize_entity_name(query)
    regex = re.compile(f".*{re.escape(normalized_query)}.*", re.IGNORECASE)

    pipeline = [
        {"$unwind": "$entities"},
        {"$match": {
            "$or": [
                {"entities.text": regex},
                {"entities.label": regex}
            ],
            "entities.text": {"$exists": True},
            "entities.label": {"$exists": True}
        }},
        {"$group": {
            "_id": "$entities.label",
            "type": {"$first": "$entities.type"},
            "count": {"$sum": 1},
            "sample_text": {"$first": "$entities.text"},
            "wikidata_id": {"$first": "$entities.wikidata_id"},
            "description": {"$first": "$entities.description"}
        }},
        {"$sort": {"count": -1, "_id": 1}},
        {"$limit": 10},
        {"$project": {
            "text": "$sample_text",  # Display text
            "label": "$_id",         # Normalized label
            "type": 1,
            "count": 1,
            "wikidata_id": 1,
            "description": 1,
            "_id": 0
        }}
    ]

    try:
        suggestions = list(collection.aggregate(pipeline))
        return {"results": suggestions}  # Single-level response
    
    except Exception as e:
        print(f"Error in suggest_entities: {e}")
        return {"results": []}  # Single-level response on error

def calculate_score(label, display, query):
    """Helper function to calculate match quality score"""
    norm_label = normalize_entity_name(label)
    norm_display = normalize_entity_name(display)
    norm_query = normalize_entity_name(query)
    
    if norm_label.startswith(norm_query):
        return 100
    if norm_display.startswith(norm_query):
        return 90
    if norm_query in norm_label:
        return 80
    return 70 - len(label)

