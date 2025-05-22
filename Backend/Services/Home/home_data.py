import os
from pymongo import MongoClient
from dotenv import load_dotenv
import re

load_dotenv()

# ===== Database Connection Setup =====
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["test_articles"]

def normalize_entity_name(entity_name):
    """Helper function to normalize entity names for comparison"""
    return entity_name.lower().strip()

def select_best_image(images):
    """Select the highest resolution image available"""
    if not images:
        return None
    resolution_order = ['1536', '1586', '1526', '1024', '840', '800', '640', '480', '320', '240']
    for res in resolution_order:
        for img in images:
            if f"/{res}/" in img:
                return img
    return images[0]

# ===== Homepage Data Functions =====
def get_recent_articles(limit=10):
    """Fetch most recent articles with normalized entity labels"""
    pipeline = [
        # Only include documents that have non-empty entities array
        {"$match": {"entities": {"$exists": True, "$ne": []}}},
        {"$sort": {"date": -1}},
        {"$limit": limit},
        {"$project": {
            "title": 1,
            "url": 1,
            "date": 1,
            "_id": 1,
            "images": 1,
            "entities": {
                "$filter": {
                    "input": "$entities",
                    "as": "ent",
                    "cond": {"$and": [
                        {"$ifNull": ["$$ent.text", False]},
                        {"$ifNull": ["$$ent.label", False]}
                    ]}
                }
            }
        }}
    ]
    
    articles = list(collection.aggregate(pipeline))
    
    processed_articles = []
    for article in articles:
        # Process entities to use normalized labels
        processed_entities = []
        for ent in article.get("entities", []):
            normalized_label = ent.get("label", ent.get("text", ""))
            processed_entities.append({
                "text": ent.get("text"),
                "normalized_label": normalized_label,
                "type": ent.get("type"),
                "wikidata_id": ent.get("wikidata_id"),
                "description": ent.get("description")
            })
        
        processed_articles.append({
            "_id": str(article["_id"]),
            "title": article["title"],
            "url": article["url"],
            "date": article.get("date"),
            "image": select_best_image(article.get("images", [])),
            "entities": processed_entities[:3]  # Limit to 3 entities for display
        })
    
    return processed_articles

def get_popular_entities(limit=10):
    """Fetch most frequently mentioned entities with normalized labels"""
    pipeline = [
        {"$unwind": "$entities"},
        # Only count entities that have both text and label
        {"$match": {
            "entities.text": {"$exists": True},
            "entities.label": {"$exists": True}
        }},
        # Group by normalized label (not by raw text)
        {"$group": {
            "_id": {
                "normalized_label": "$entities.label",
                "type": "$entities.type"
            },
            "count": {"$sum": 1},
            # Keep sample data for display
            "sample_text": {"$first": "$entities.text"},
            "wikidata_id": {"$first": "$entities.wikidata_id"},
            "description": {"$first": "$entities.description"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {
            "normalized_label": "$_id.normalized_label",
            "type": "$_id.type",
            "count": 1,
            "sample_text": 1,
            "wikidata_id": 1,
            "description": 1,
            "_id": 0
        }}
    ]
    
    entities = list(collection.aggregate(pipeline))
    
    # Add ranking information
    ranked_entities = []
    for i, entity in enumerate(entities, 1):
        ranked_entity = {
            "rank": i,
            **entity
        }
        ranked_entities.append(ranked_entity)
    
    return ranked_entities

def get_important_relations(limit=5):
    """Fetch important relationships between entities"""
    pipeline = [
        {"$unwind": "$entities"},
        {"$match": {
            "entities.label": {"$exists": True},
            "entities.relations": {"$exists": True, "$ne": []}
        }},
        {"$unwind": "$entities.relations"},
        {"$group": {
            "_id": {
                "source": "$entities.label",
                "target": "$entities.relations.target",
                "relation": "$entities.relations.type"
            },
            "count": {"$sum": 1},
            "source_type": {"$first": "$entities.type"},
            "target_type": {"$first": "$entities.relations.target_type"},
            "sample_sentence": {"$first": "$entities.relations.sentence"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {
            "source": "$_id.source",
            "target": "$_id.target",
            "relation": "$_id.relation",
            "source_type": 1,
            "target_type": 1,
            "count": 1,
            "sample_sentence": 1,
            "_id": 0
        }}
    ]
    
    return list(collection.aggregate(pipeline))

def get_homepage_data():
    """Combined endpoint for all homepage data with normalized entities"""
    return {
        "recent_articles": get_recent_articles(),
        "popular_entities": get_popular_entities(),
        "important_relations": get_important_relations()
    }
