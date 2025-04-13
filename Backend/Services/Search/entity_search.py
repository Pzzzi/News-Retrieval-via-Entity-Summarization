import os
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ====== Database Connections ======
# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Neo4j Connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# === Neo4j: Get Related Entities and Their Related Entities ===
def get_related_entities(entity_name):
    query = """
    MATCH (e:Entity {name: $entity})-[:RELATIONSHIP]-(related)-[:RELATIONSHIP]-(related2)
    WHERE related2.name <> $entity
    RETURN DISTINCT related.name AS related_name, related.type AS related_type,
                    related2.name AS related2_name, related2.type AS related2_type
    LIMIT 20
    """
    with driver.session() as session:
        result = session.run(query, entity=entity_name)
        
        nodes = {entity_name: {"id": entity_name}}  
        links = set()

        for record in result:
            related = record["related_name"]
            related_type = record["related_type"]
            related2 = record["related2_name"]
            related2_type = record["related2_type"]

            # Add nodes
            nodes[related] = {"id": related, "type": related_type}
            nodes[related2] = {"id": related2, "type": related2_type}

            # Add links: Main -> Related, Related -> Related2
            links.add((entity_name, related))  # Main -> Related
            links.add((related, related2))     # Related -> Related2

        return {"nodes": list(nodes.values()), "links": [{"source": s, "target": t} for s, t in links]}

# === MongoDB: Search Articles with Ranking ===
def search_articles_by_entity(entity_name, related_entities):
    """Fetch articles mentioning the entity & related entities, ranked by relevance."""
    search_terms = [entity_name] + [e["id"] for e in related_entities]
    
    pipeline = [
        {"$match": {"entities.text": {"$in": search_terms}}},
        {"$addFields": {
            "entity_mention_count": {
                "$size": {
                    "$filter": {
                        "input": "$entities",
                        "as": "ent",
                        "cond": {"$in": ["$$ent.text", search_terms]}
                    }
                }
            }
        }},
        {"$sort": {"entity_mention_count": -1, "date": -1}},
        {"$limit": 10},
        {"$project": {
            "title": 1,
            "url": 1,
            "date": 1,
            "_id": 1,
            "images": 1,
            "entity_mention_count": 1
        }}
    ]
    
    articles = list(collection.aggregate(pipeline))

    def get_best_image(images):
        if not images:
            return None
            
        # BBC-specific logic - look for highest resolution
        resolution_order = ['1536', '1586', '1526', '1024', '840', '800', '640', '480', '320', '240']
        
        for res in resolution_order:
            for img in images:
                if f"/{res}/" in img:
                    return img
        return images[0]  # Fallback to first image if no resolution matches

    return [{
        "_id": str(article["_id"]),
        "title": article["title"],
        "url": article["url"],
        "date": article.get("date"),
        "image": get_best_image(article.get("images")) if article.get("images") else None
    } for article in articles]

# === Query Suggestion When No Results Are Found ===
def suggest_alternative_entities(entity_name):
    """Suggest similar entities when no results are found."""
    query = """
    MATCH (e:Entity)
    WHERE e.name CONTAINS $entity
    RETURN e.name AS name, e.type AS type
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(query, entity=entity_name)
        return [{"id": record["name"], "type": record["type"]} for record in result]

# === Unified Search Function ===
def entity_search(entity_name):
    """Fetch related entities, ranked articles, and handle no-result cases."""
    
    related_entities_data = get_related_entities(entity_name)
    related_entities = related_entities_data["nodes"]
    links = related_entities_data["links"]
    articles = search_articles_by_entity(entity_name, related_entities)

    if not articles:
        # No results? Suggest similar entities instead
        suggestions = suggest_alternative_entities(entity_name)
        return {
            "entity": {"id": entity_name},
            "related_entities": related_entities,
            "articles": [],
            "suggestions": suggestions,
            "links": links
        }

    return {
        "entity": {"id": entity_name},
        "related_entities": related_entities,
        "articles": articles,
        "links": links
    }



