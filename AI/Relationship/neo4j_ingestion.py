from pymongo import MongoClient
from neo4j import GraphDatabase
from collections import defaultdict

# MongoDB Connection
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Neo4j Connection (Update with your credentials)
NEO4J_URI = "neo4j+s://a2db5be7.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "d58VQZXosR0wt5AktACNvRlWFHfVjPVskcSqkyUgN78"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def batch_create_entities(tx, entities_batch):
    """Creates entity nodes in Neo4j with their correct labels."""
    query = """
    UNWIND $entities AS entity
    CALL apoc.create.node([entity.label], {name: entity.name}) YIELD node
    RETURN node
    """
    tx.run(query, entities=entities_batch)

def batch_create_relationships(tx, relationships_batch):
    """Creates relationships between entities in bulk."""
    query = """
    UNWIND $relationships AS rel
    MATCH (e1 {name: rel.entity1})
    MATCH (e2 {name: rel.entity2})
    MERGE (e1)-[r:MENTIONED_WITH]->(e2)
    ON CREATE SET r.count = rel.count
    ON MATCH SET r.count = r.count + rel.count
    """
    tx.run(query, relationships=relationships_batch)

def import_entities_to_neo4j(batch_size=500):
    """Extracts entities from MongoDB & inserts them into Neo4j in batches."""
    entities_set = set()  # Track unique entities
    relationships_dict = defaultdict(int)  # Track entity co-occurrences

    # Process each article in batches
    entity_batch = []
    for article in collection.find():
        entities = article.get("entities", [])
        unique_entities = {(ent["text"], ent["label"]) for ent in entities}  # Remove duplicates per article
        
        # Add entities to batch
        for name, label in unique_entities:
            if name not in entities_set:
                entity_batch.append({"name": name, "label": label})
                entities_set.add(name)
        
        # Track relationships
        for i in range(len(entities)):
            for j in range(i + 1, len(entities)):  # Avoid self-loops
                entity1, entity2 = entities[i]["text"], entities[j]["text"]
                relationships_dict[(entity1, entity2)] += 1
        
        # Insert entities in batches
        if len(entity_batch) >= batch_size:
            with driver.session() as session:
                session.execute_write(batch_create_entities, entity_batch)
            entity_batch = []  # Reset batch

    # Insert remaining entities
    if entity_batch:
        with driver.session() as session:
            session.execute_write(batch_create_entities, entity_batch)

    # Convert relationships dictionary to list format for bulk insert
    relationships_batch = [
        {"entity1": e1, "entity2": e2, "count": count}
        for (e1, e2), count in relationships_dict.items()
    ]

    # Insert relationships in batches
    batch_size = 500
    for i in range(0, len(relationships_batch), batch_size):
        batch = relationships_batch[i:i+batch_size]
        with driver.session() as session:
            session.execute_write(batch_create_relationships, batch)

import_entities_to_neo4j()
print("🎉 Bulk Entity Ingestion Complete with Correct Labels!")

# Close Neo4j connection
driver.close()



