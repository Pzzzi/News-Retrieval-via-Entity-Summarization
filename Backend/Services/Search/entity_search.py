from pymongo import MongoClient
from neo4j import GraphDatabase

# === Database Connections ===
# MongoDB
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["articles"]

# Neo4j
NEO4J_URI = "neo4j+s://a2db5be7.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "d58VQZXosR0wt5AktACNvRlWFHfVjPVskcSqkyUgN78"
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
    articles = collection.find(query, {"title": 1, "url": 1, "_id": 0}).limit(10)
    return list(articles)


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