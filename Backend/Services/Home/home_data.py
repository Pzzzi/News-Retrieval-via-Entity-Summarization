import os
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv
import re

load_dotenv()

# ===== Database Connection Setup =====
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def normalize_entity_name(entity_name):
    """Helper function to normalize entity names for comparison"""
    return entity_name.lower().strip()

def get_best_image(images):
    if not images:
        return None

    def parse_resolution(url):
        match = re.search(r'/(\d+)x(\d+)/', url)
        if match:
            return int(match.group(1)), int(match.group(2))
        return None

    # Filter out low-quality or square images
    filtered_images = []
    for img in images:
        res = parse_resolution(img)
        if res:
            width, height = res
            if width >= 200 and height >= 200 and abs(width - height) > 20:
                area = width * height
                filtered_images.append((area, img))

    if filtered_images:
        # Return image with largest area
        return max(filtered_images, key=lambda x: x[0])[1]

    # Fallback: use original resolution order logic
    resolution_order = ['1536', '1586', '1526', '1024', '840', '800', '640', '480', '320', '240']
    for res in resolution_order:
        for img in images:
            if f"/{res}/" in img:
                return img

    return images[0]

# Add a new endpoint for paginated articles
def get_paginated_articles(page=1, per_page=9):
    """Get articles with pagination support"""
    return get_recent_articles(limit=per_page, page=page)

# ===== Homepage Data Functions =====
def get_recent_articles(limit=9, page=1):
    """Fetch most recent articles with normalized entity labels"""
    skip = (page - 1) * limit
    pipeline = [
        # Only include documents that have non-empty entities array
        {"$match": {"entities": {"$exists": True, "$ne": []}}},
        {"$sort": {"date": -1}},
        {"$skip": skip},
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
            "image": get_best_image(article.get("images", [])),
            "entities": processed_entities[:3]  # Limit to 3 entities for display
        })
    
    return processed_articles

def get_popular_entities(limit=10):
    """
    Fetch most frequently occurring entities from Neo4j with type, label, and metadata.
    """
    query = """
    MATCH (e:Entity)
    OPTIONAL MATCH (e)-[r]->()
    WITH e, count(r) AS relation_count
    RETURN 
        e.name AS normalized_label,
        e.type AS type,
        e.wikidataId AS wikidata_id,
        e.description AS description,
        relation_count AS count
    ORDER BY count DESC
    LIMIT $limit
    """
    
    with driver.session() as session:
        result = session.run(query, limit=limit)
        entities = []
        for i, record in enumerate(result, 1):
            entities.append({
                "rank": i,
                "normalized_label": record["normalized_label"],
                "type": record["type"],
                "count": record["count"],
                "wikidata_id": record.get("wikidata_id", ""),
                "description": record.get("description", "")
            })
    return entities

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
