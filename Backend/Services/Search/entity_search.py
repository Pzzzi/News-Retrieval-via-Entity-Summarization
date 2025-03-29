import os
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ====== Database Connections ======
# MongoDB Connection
MONGO_URI=os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Neo4j Connection
NEO4J_URI=os.getenv("NEO4J_URI")
NEO4J_USER=os.getenv("NEO4J_USER")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


# === Neo4j: Get Related Entities with Types ===
def get_related_entities(entity_name):
    query = """
    MATCH (e:Entity {name: $entity})-[:RELATIONSHIP]-(related)
    RETURN DISTINCT related.name AS name, related.type AS type
    LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, entity=entity_name)
        return [{"id": record["name"], "type": record["type"]} for record in result]


# === MongoDB: Get Articles ===
def search_articles_by_entity(entity_name, related_entities):
    search_terms = [entity_name] + [e["id"] for e in related_entities]
    query = {"entities.text": {"$in": search_terms}}
    articles = collection.find(query, {"title": 1, "url": 1, "_id": 1}).limit(10)

    # Convert ObjectId to string
    return [{"_id": str(article["_id"]), "title": article["title"], "url": article["url"]} for article in articles]


# === Unified Search Function ===
def entity_search(entity_name):
    """Fetch related entities + articles."""
    related_entities = get_related_entities(entity_name)
    articles = search_articles_by_entity(entity_name, related_entities)

    return {
        "entity": {"id": entity_name},
        "related_entities": related_entities,
        "articles": articles
    }