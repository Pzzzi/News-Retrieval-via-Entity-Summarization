import os
import spacy
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

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# === Relationship Filtering Rules ===
INVALID_VERBS = {"come", "have", "make", "step", "smile", "say", "told", "report", "describe"}
VALID_ENTITY_PAIRS = {
    ("PERSON", "ORG"), ("ORG", "ORG"), ("ORG", "GPE"), ("GPE", "ORG"), ("PERSON", "GPE"),
    ("EVENT", "DATE"), ("PRODUCT", "ORG")
}

# ====== Create Entities in Neo4j ======
def create_entity(tx, name, label):
    query = """
    MERGE (e:Entity {name: $name})
    ON CREATE SET e.type = $label
    """
    tx.run(query, name=name, label=label)

# ====== Create Relationships in Neo4j ======
def create_relationship(tx, entity1, entity2, rel_type):
    query = """
    MATCH (e1:Entity {name: $entity1})
    MATCH (e2:Entity {name: $entity2})
    MERGE (e1)-[r:RELATIONSHIP {type: $rel_type}]->(e2)
    ON CREATE SET r.weight = 1
    ON MATCH SET r.weight = r.weight + 1
    """
    tx.run(query, entity1=entity1, entity2=entity2, rel_type=rel_type)

# ====== Relationship Extraction with Context ======
def extract_relationships(doc, entities):
    """Automatically detect relationships using dependency parsing and context filtering."""
    relationships = []
    entity_map = {ent["text"]: ent["label"] for ent in entities}
    sentences = list(doc.sents)

    for sent in sentences:
        sent_text = sent.text
        sent_doc = nlp(sent_text)

        entity_pairs = [(e1, e2) for e1 in entity_map for e2 in entity_map if e1 != e2 and e1 in sent_text and e2 in sent_text]

        for e1, e2 in entity_pairs:
            label1, label2 = entity_map[e1], entity_map[e2]

            # Filter out invalid entity pairs
            if (label1, label2) not in VALID_ENTITY_PAIRS and (label2, label1) not in VALID_ENTITY_PAIRS:
                continue  

            # Identify valid verbs between entities
            rel_type = None
            for token in sent_doc:
                if token.head.text in {e1, e2} and token.pos_ == "VERB":
                    verb = token.lemma_.upper()
                    
                    if verb not in INVALID_VERBS:
                        rel_type = verb
                        break  # Stop at the first valid relationship

            # Only create a relationship if a valid verb is found
            if rel_type:
                relationships.append((e1, e2, rel_type))

    return relationships

# ====== Main Ingestion Function ======
def import_entities_and_relationships():
    """Ingest entities and auto-detected relationships into Neo4j."""
    with driver.session() as session:
        for article in collection.find():
            content = article.get("content", "")
            entities = article.get("entities", [])

            # Step 1: Create Entity Nodes
            for entity in entities:
                session.write_transaction(create_entity, entity["text"], entity["label"])

            # Step 2: Extract Relationships with Context Awareness
            doc = nlp(content)
            relationships = extract_relationships(doc, entities)

            # Step 3: Create Relationships in Neo4j
            for e1, e2, rel_type in relationships:
                session.write_transaction(create_relationship, e1, e2, rel_type)

    print("✅ Refined Relationship Extraction Complete!")

# ====== Run the Ingestion ======
import_entities_and_relationships()
driver.close()
print("🎉 Neo4j connection closed.")
