from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from neo4j import GraphDatabase

app = Flask(__name__)
CORS(app)  # Allows React to call Flask API

# MongoDB Connection
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["news_db"]
collection = db["articles"]

# Neo4j Connection 
NEO4J_URI = "neo4j+s://a2db5be7.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "d58VQZXosR0wt5AktACNvRlWFHfVjPVskcSqkyUgN78"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_related_entities(entity_name):
    """Find related entities from Neo4j."""
    query = """
    MATCH (e:Entity {name: $name})-[:MENTIONED_WITH]-(related)
    RETURN DISTINCT related.name LIMIT 10
    """
    with driver.session() as session:
        result = session.run(query, name=entity_name)
        return [record["related.name"] for record in result]

def search_articles_by_entity(entity_name, related_entities):
    """Find articles in MongoDB that mention the entity or related entities."""
    search_terms = [entity_name] + related_entities
    query = {"entities.text": {"$in": search_terms}}
    articles = collection.find(query, {"title": 1, "url": 1, "_id": 0}).limit(10)
    return list(articles)

@app.route("/search", methods=["GET"])
def search():
    """Search for articles based on an entity."""
    entity = request.args.get("entity")
    if not entity:
        return jsonify({"error": "Entity parameter is required"}), 400

    related_entities = get_related_entities(entity)
    articles = search_articles_by_entity(entity, related_entities)

    return jsonify({
        "entity": entity,
        "related_entities": related_entities,
        "articles": articles
    })

if __name__ == "__main__":
    app.run(debug=True)
