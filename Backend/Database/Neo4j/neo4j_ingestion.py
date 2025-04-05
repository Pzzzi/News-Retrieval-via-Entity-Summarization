import os
import spacy
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ====== Database Connections ======
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

nlp = spacy.load("en_core_web_sm")

INVALID_VERBS = {"come", "have", "make", "step", "smile", "say", "told", "report", "describe"}
VALID_ENTITY_PAIRS = {
    ("PERSON", "ORG"), ("ORG", "ORG"), ("ORG", "GPE"), ("GPE", "ORG"), ("PERSON", "GPE"),
    ("EVENT", "DATE"), ("PRODUCT", "ORG")
}

# ====== Neo4j Queries ======
def create_entity(tx, name, label):
    query = """
    MERGE (e:Entity {name: $name})
    ON CREATE SET e.type = [$label]
    ON MATCH SET e.type = CASE 
        WHEN NOT $label IN e.type THEN e.type + [$label]
        ELSE e.type
    END
    """
    tx.run(query, name=name, label=label)

def create_relationship(tx, entity1, entity2, rel_type):
    query = """
    MATCH (e1:Entity {name: $entity1})
    MATCH (e2:Entity {name: $entity2})
    MERGE (e1)-[r:RELATIONSHIP {type: $rel_type}]->(e2)
    ON CREATE SET r.weight = 1
    ON MATCH SET r.weight = r.weight + 1
    """
    tx.run(query, entity1=entity1, entity2=entity2, rel_type=rel_type)

def extract_relationships(doc, entities):
    """Extract relationships between entities using NLP."""
    relationships = []
    entity_map = {ent["text"]: ent["label"] for ent in entities}

    for sent in doc.sents:
        sent_doc = nlp(sent.text)
        entity_pairs = [(e1, e2) for e1 in entity_map for e2 in entity_map if e1 != e2 and e1 in sent.text and e2 in sent.text]

        for e1, e2 in entity_pairs:
            label1, label2 = entity_map[e1], entity_map[e2]
            if (label1, label2) not in VALID_ENTITY_PAIRS and (label2, label1) not in VALID_ENTITY_PAIRS:
                continue  

            rel_type = None
            for token in sent_doc:
                if token.head.text in {e1, e2} and token.pos_ == "VERB":
                    verb = token.lemma_.upper()
                    if verb not in INVALID_VERBS:
                        rel_type = verb
                        break  

            if rel_type:
                relationships.append((e1, e2, rel_type))

    return relationships

# ====== Main Ingestion Function ======
def import_entities_and_relationships():
    """Ingest new entities and relationships into Neo4j."""
    with driver.session() as session:
        for article in collection.find({"entities": {"$exists": True}, "neo4j_processed": {"$exists": False}}):
            content = article.get("content", "")
            entities = article.get("entities", [])

            if not entities:
                continue  # Skip if no entities

            # Step 1: Create Entities
            for entity in entities:
                session.write_transaction(create_entity, entity["text"], entity["label"])

            # Step 2: Extract Relationships
            doc = nlp(content)
            relationships = extract_relationships(doc, entities)

            # Step 3: Create Relationships
            for e1, e2, rel_type in relationships:
                session.write_transaction(create_relationship, e1, e2, rel_type)

            # Mark as processed
            collection.update_one({"_id": article["_id"]}, {"$set": {"neo4j_processed": True}})

    print("✅ Relationship Ingestion Complete!")

# ====== Run the Ingestion ======
try:
    import_entities_and_relationships()
finally:
    driver.close()
    print("🎉 Neo4j connection closed.")

