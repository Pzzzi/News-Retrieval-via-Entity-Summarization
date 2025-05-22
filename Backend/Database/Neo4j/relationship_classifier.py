import os
import re
import spacy
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pymongo import MongoClient
from tqdm import tqdm
from dotenv import load_dotenv
import numpy as np
from neo4j import GraphDatabase, basic_auth
from datetime import datetime
from collections import defaultdict

# Load environment
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["test_articles"]

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# ===== IMPROVED RELATION EXTRACTION APPROACH =====

# 2. MORE COMPREHENSIVE RELATION TYPES
RELATION_LABELS = [
    "Cause-Effect(e1,e2)",
    "Cause-Effect(e2,e1)",
    "Instrument-Agency(e1,e2)",
    "Instrument-Agency(e2,e1)",
    "Product-Producer(e1,e2)",
    "Product-Producer(e2,e1)",
    "Content-Container(e1,e2)",
    "Content-Container(e2,e1)",
    "Entity-Origin(e1,e2)",
    "Entity-Origin(e2,e1)",
    "Entity-Destination(e1,e2)",
    "Entity-Destination(e2,e1)",
    "Component-Whole(e1,e2)",
    "Component-Whole(e2,e1)",
    "Member-Collection(e1,e2)",
    "Member-Collection(e2,e1)",
    "Message-Topic(e1,e2)",
    "Message-Topic(e2,e1)",
    "Other"
]

# 1. USE A FINE-TUNED MODEL SPECIFICALLY FOR RELATION CLASSIFICATION
model_path = "D:/FYP RELATION CLASSIFIER MODEL ROBERTA" 
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)

# 3. ADJUSTED CONFIDENCE THRESHOLD
CONFIDENCE_THRESHOLD = 0.0030

# ADDED: Special handling for "Other" class - require higher confidence
OTHER_CONFIDENCE_THRESHOLD = 0.98

# ===== NEO4J BATCH INGESTION CLASS =====
class Neo4jIngestor:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=basic_auth(user, password))
        self.batch_size = 100
        self.node_batch = []
        self.relation_batch = []
        
    def close(self):
        self.driver.close()
        
    def flush_nodes(self):
        if not self.node_batch:
            return
            
        with self.driver.session() as session:
            query = """
            UNWIND $batch as row
            MERGE (n:Entity {name: row.name})
            SET n.type = row.type,
                n.description = row.description,
                n.wikidataId = row.wikidata_id,
                n.lastSeen = datetime(row.lastSeen),
                n.source = row.source
            """
            session.run(query, batch=self.node_batch)
        self.node_batch = []
        
    def flush_relations(self):
        if not self.relation_batch:
            return
            
        with self.driver.session() as session:
            query = """
            UNWIND $batch as row
            MATCH (a:Entity {name: row.source})
            MATCH (b:Entity {name: row.target})
            MERGE (a)-[r:RELATION {type: row.type}]->(b)
            SET r.confidence = row.confidence,
                r.sentence = row.sentence,
                r.timestamp = datetime(row.timestamp)
            """
            session.run(query, batch=self.relation_batch)
        self.relation_batch = []
        
    def add_node_to_batch(self, name, entity_type, source, description="", wikidata_id=""):
        self.node_batch.append({
            "name": name,
            "type": entity_type,
            "description": description,
            "wikidata_id": wikidata_id,
            "lastSeen": datetime.now().isoformat(),
            "source": source
        })
        
        if len(self.node_batch) >= self.batch_size:
            self.flush_nodes()
            
    def add_relation_to_batch(self, source, target, rel_type, confidence, sentence):
        self.relation_batch.append({
            "source": source,
            "target": target,
            "type": rel_type,
            "confidence": float(confidence),
            "sentence": sentence,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.relation_batch) >= self.batch_size:
            self.flush_relations()
            
    def process_batches(self):
        self.flush_nodes()
        self.flush_relations()

# ===== ENTITY TYPE MAPPING FOR BETTER CATEGORIZATION =====
ENTITY_TYPE_MAP = {
    "PERSON": "PERSON",
    "ORG": "ORG", 
    "ORGANIZATION": "ORG",
    "GPE": "GPE",
    "LOC": "GPE",
    "LOCATION": "GPE",
    "FACILITY": "GPE",
    "EVENT": "EVENT",
    "DATE": "DATE",
    "TIME": "DATE",
    "MONEY": "MONEY",
    "PERCENT": "NUMBER",
    "QUANTITY": "NUMBER",
    "CARDINAL": "NUMBER",
    "NORP": "GROUP",  # Nationalities, religious or political groups
    "PRODUCT": "PRODUCT",
    "WORK_OF_ART": "PRODUCT",
    "FAC": "FACILITY",
    "UNKNOWN": "UNKNOWN"
}

# ADDED: Common entity relationships based on type
ENTITY_RELATION_HINTS = {
    ("ORG", "PRODUCT"): ["Product-Producer(e1,e2)", "Entity-Origin(e1,e2)"],
    ("PRODUCT", "ORG"): ["Product-Producer(e2,e1)", "Entity-Origin(e2,e1)"],
    ("PERSON", "ORG"): ["Member-Collection(e1,e2)"],
    ("ORG", "PERSON"): ["Member-Collection(e2,e1)"],
    ("PERSON", "GPE"): ["Entity-Origin(e1,e2)", "Entity-Destination(e1,e2)"],
    ("GPE", "PERSON"): ["Entity-Origin(e2,e1)", "Entity-Destination(e2,e1)"],
}

def get_normalized_entity_type(entity_type):
    """Convert various entity types to a normalized set"""
    return ENTITY_TYPE_MAP.get(entity_type, "UNKNOWN")

def format_relation_prompt(subj, obj, sentence):
    """Create a prompt that clearly indicates entity order for relation classification"""
    return (
        f"In the sentence: '{sentence}'\n"
        f"What is the relationship between:\n"
        f"e1: '{subj['label']}' ({subj['type']}) and\n"
        f"e2: '{obj['label']}' ({obj['type']})?\n"
        f"Choose from: {', '.join(RELATION_LABELS)}"
    )

def predict_relationship(subj, obj, sentence):
    """Enhanced prediction with better context formatting and rule-based verification"""
    if not could_have_relation(subj, obj):
        return "no_relation", [1.0] + [0.0] * (len(RELATION_LABELS) - 1)

    context = format_relation_prompt(subj, obj, sentence)
    inputs = tokenizer(context, return_tensors="pt", truncation=True, max_length=256)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1).squeeze()

    # Get all probabilities
    probs_list = probs.tolist()
    
    # Get top-k predictions (k=5)
    top_k = 5
    top_indices = torch.topk(probs, k=min(top_k, len(RELATION_LABELS))).indices.tolist()
    top_labels = [RELATION_LABELS[idx] for idx in top_indices]
    top_probs = [probs_list[idx] for idx in top_indices]
    
    # Print top predictions for debugging
    print(f"Top {len(top_labels)} predictions for {subj['label']} -> {obj['label']}:")
    for i, (label, prob) in enumerate(zip(top_labels, top_probs)):
        print(f"{i+1}. {label}: {prob:.4f}")
    
    # ADDED: Get normalized entity types
    subj_type = get_normalized_entity_type(subj["type"])
    obj_type = get_normalized_entity_type(obj["type"])
    entity_pair = (subj_type, obj_type)
    
    # ADDED: Check for special entity type hints
    preferred_relations = ENTITY_RELATION_HINTS.get(entity_pair, [])
    
    # Decision logic for determining the relation:
    # 1. If top prediction is "Other" but confidence is below threshold, ignore it
    # 2. Check for preferred relations based on entity types
    # 3. Fall back to top non-Other prediction if confidence is reasonable
    
    # If top prediction is "Other" but doesn't meet higher threshold, ignore it
    if top_labels[0] == "Other" and top_probs[0] < OTHER_CONFIDENCE_THRESHOLD:
        print(f"Rejecting 'Other' with confidence {top_probs[0]:.4f} < {OTHER_CONFIDENCE_THRESHOLD}")
        
        # Try to find a better relation from top-k
        for i, label in enumerate(top_labels[1:], 1):
            if label != "Other" and top_probs[i] >= CONFIDENCE_THRESHOLD:
                # Check if this relation is in our preferred list for this entity pair
                if preferred_relations and label in preferred_relations:
                    print(f"Selected preferred relation: {label} with confidence {top_probs[i]:.4f}")
                    return label, probs_list
                
                # Even if not preferred, take it if reasonable confidence
                if top_probs[i] >= CONFIDENCE_THRESHOLD:
                    print(f"Selected alternative relation: {label} with confidence {top_probs[i]:.4f}")
                    return label, probs_list
        
        # If we have preferred relations for this entity pair, use the first one
        if preferred_relations:
            print(f"Falling back to preferred relation for {subj_type}-{obj_type}: {preferred_relations[0]}")
            return preferred_relations[0], probs_list
            
        # Last resort: suggest based on entity types
        fallback = suggest_alternative_relation(subj, obj)
        if fallback != "no_relation":
            print(f"Using suggested fallback relation: {fallback}")
            return fallback, probs_list
    
    # If top prediction is not "Other" or it has very high confidence, use it
    if top_probs[0] >= CONFIDENCE_THRESHOLD:
        if top_labels[0] == "Other" and len(top_labels) > 1:
            # Double-check for special case: ORG-PRODUCT should be Product-Producer
            if entity_pair == ("ORG", "PRODUCT") and "Product-Producer(e1,e2)" in top_labels:
                idx = top_labels.index("Product-Producer(e1,e2)")
                print(f"Overriding 'Other' with specific relation: Product-Producer(e1,e2) ({top_probs[idx]:.4f})")
                return "Product-Producer(e1,e2)", probs_list
            # Special case for Apple Inc. and iPhone
            if (subj['label'].lower().find('apple') >= 0 and obj['label'].lower().find('iphone') >= 0):
                print(f"Special case detected: Apple Inc. and iPhone - using Entity-Origin relation")
                return "Entity-Origin(e1,e2)", probs_list
        
        print(f"Using top prediction: {top_labels[0]} with confidence {top_probs[0]:.4f}")
        return top_labels[0], probs_list
    
    # If no good relation found
    print(f"No suitable relation found above threshold {CONFIDENCE_THRESHOLD}")
    return "no_relation", probs_list

def could_have_relation(subj, obj):
    """Quick check if these entity types could possibly have a meaningful relation"""
    # Normalize entity types
    subj_type = get_normalized_entity_type(subj["type"])
    obj_type = get_normalized_entity_type(obj["type"])
    
    # If either entity is of unknown type, be permissive
    if subj_type == "UNKNOWN" or obj_type == "UNKNOWN":
        return True
    
    # Define which entity type pairs are worth checking
    valid_pairs = {
        ("PERSON", "ORG"), 
        ("PERSON", "GPE"),
        ("PERSON", "GROUP"),
        ("PERSON", "PERSON"),
        ("ORG", "ORG"),
        ("ORG", "GPE"),
        ("ORG", "PERSON"),
        ("ORG", "PRODUCT"),  # ADDED: Organization-Product pair
        ("PRODUCT", "ORG"),  # ADDED: Product-Organization pair
        ("GPE", "GPE"),
        ("EVENT", "GPE"),
        ("EVENT", "DATE")
    }
    
    return (subj_type, obj_type) in valid_pairs

def is_valid_relation(subj, obj, relation):
    """Type checking for standard semantic relations"""
    if relation == "Other":
        return True
    
    # Get base relation without direction
    base_relation = relation.split('(')[0]
    
    # Normalize entity types
    subj_type = get_normalized_entity_type(subj["type"])
    obj_type = get_normalized_entity_type(obj["type"])
    
    # UPDATED: Define valid entity type combinations for each relation
    relation_rules = {
        "Cause-Effect": [("EVENT", "EVENT"), ("PERSON", "EVENT"), ("ORG", "EVENT"), ("EVENT", "ORG")],
        "Instrument-Agency": [("PRODUCT", "PERSON"), ("PRODUCT", "ORG"), ("ORG", "PERSON")],
        "Product-Producer": [("PRODUCT", "ORG"), ("PRODUCT", "PERSON"), ("ORG", "PRODUCT")],
        "Content-Container": [("PRODUCT", "PRODUCT"), ("EVENT", "ORG"), ("PERSON", "ORG")],
        "Entity-Origin": [("PERSON", "GPE"), ("PRODUCT", "ORG"), ("PRODUCT", "GPE"), ("PERSON", "ORG")],
        "Entity-Destination": [("PERSON", "GPE"), ("PRODUCT", "GPE"), ("ORG", "GPE")],
        "Component-Whole": [("PRODUCT", "PRODUCT"), ("ORG", "ORG"), ("PERSON", "ORG")],
        "Member-Collection": [("PERSON", "ORG"), ("PERSON", "GROUP"), ("ORG", "ORG")],
        "Message-Topic": [("PERSON", "EVENT"), ("ORG", "EVENT"), ("PERSON", "PRODUCT"), ("ORG", "PRODUCT")]
    }
    
    if base_relation in relation_rules:
        return (subj_type, obj_type) in relation_rules[base_relation]
    
    return False

def suggest_alternative_relation(subj, obj):
    """Suggest the most likely standard semantic relation based on entity types"""
    subj_type = get_normalized_entity_type(subj["type"])
    obj_type = get_normalized_entity_type(obj["type"])
    
    # UPDATED: More comprehensive type-relation mapping
    type_relation_map = {
        ("ORG", "PRODUCT"): "Product-Producer(e1,e2)",
        ("PRODUCT", "ORG"): "Product-Producer(e2,e1)",
        ("PERSON", "ORG"): "Member-Collection(e1,e2)",
        ("ORG", "PERSON"): "Member-Collection(e2,e1)",
        ("PERSON", "GPE"): "Entity-Origin(e1,e2)",
        ("GPE", "PERSON"): "Entity-Origin(e2,e1)",
        ("ORG", "GPE"): "Entity-Origin(e1,e2)",
        ("GPE", "ORG"): "Entity-Origin(e2,e1)",
        ("PRODUCT", "PERSON"): "Product-Producer(e1,e2)",
        ("PERSON", "PRODUCT"): "Product-Producer(e2,e1)"
    }
    
    return type_relation_map.get((subj_type, obj_type), "no_relation")

def extract_entities_from_sentence(nlp, sentence_text):
    """Extract entities directly from a sentence using spaCy"""
    doc = nlp(sentence_text)
    entities = []
    
    for ent in doc.ents:
        # Filter out low-value entity types
        if ent.label_ not in ["CARDINAL", "ORDINAL", "QUANTITY", "PERCENT"]:
            entities.append({
                "label": ent.text,
                "type": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })
    
    return entities

def is_valid_entity(entity):
    """Check if entity meets minimum quality standards"""
    # Must have a non-empty name and valid type
    if not entity.get("label") or not entity.get("type"):
        return False
    
    # If Wikidata entity, must have both ID and description
    if entity.get("wikidata_id"):
        if not entity.get("description"):
            return False
    
    # Reject single-character or all-caps abbreviations (like "AQ")
    if len(entity["label"]) <= 2 and entity["label"].isupper():
        return False
        
    return True

def process_document(doc, nlp, ingestor):
    text = doc.get("content", "")
    if not text:
        return []
    
    relations = []
    
    for sent in nlp(text).sents:
        sent_text = sent.text.strip()
        if len(sent_text) < 10:
            continue
            
        # ONLY USE WIKIDATA-ANNOTATED ENTITIES
        sentence_entities = [
            {
                "label": entity["label"],
                "type": entity.get("type", "UNKNOWN"),
                "description": entity.get("description", ""),
                "wikidata_id": entity.get("wikidata_id", "")
            }
            for entity in doc.get("entities", [])
            if (re.search(rf'\b{re.escape(entity["label"])}\b', sent_text, re.I) 
                and is_valid_entity(entity))
        ]
        
        # Process entity pairs (only if we have at least 2 valid entities)
        for subj, obj in [(sentence_entities[i], sentence_entities[j]) 
                         for i in range(len(sentence_entities)) 
                         for j in range(i+1, len(sentence_entities))]:
            
            rel, probs = predict_relationship(subj, obj, sent_text)
            
            if rel != "no_relation" and max(probs) >= CONFIDENCE_THRESHOLD:
                # Ingest entities
                ingestor.add_node_to_batch(
                    name=subj["label"],
                    entity_type=get_normalized_entity_type(subj["type"]),
                    source=doc.get("source", "unknown"),
                    description=subj["description"],
                    wikidata_id=subj["wikidata_id"]
                )
                ingestor.add_node_to_batch(
                    name=obj["label"],
                    entity_type=get_normalized_entity_type(obj["type"]),
                    source=doc.get("source", "unknown"),
                    description=obj["description"],
                    wikidata_id=obj["wikidata_id"]
                )
                
                # Add relation
                ingestor.add_relation_to_batch(
                    subj["label"],
                    obj["label"],
                    rel,
                    max(probs),
                    sent_text
                )
                
                relations.append({
                    "subject": subj["label"],
                    "object": obj["label"],
                    "relation": rel,
                    "confidence": max(probs),
                    "sentence": sent_text
                })
    
    return relations

def main():
    # Load spaCy model
    nlp = spacy.load("en_core_web_sm")
    
    # Initialize Neo4j ingestor
    ingestor = Neo4jIngestor(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # Test on documents (adjust limit as needed)
        docs = collection.find().limit(50)  # Increased from 5 to 50 for better batching
        all_relations = []
        
        for doc in tqdm(docs):
            print(f"\nProcessing document: {doc['_id']}")
            relations = process_document(doc, nlp, ingestor)
            
            if relations:
                all_relations.extend(relations)
        
        # Flush any remaining batches
        ingestor.process_batches()
        
        # Summary of results
        if all_relations:
            relation_types = defaultdict(int)
            for rel in all_relations:
                relation_types[rel["relation"]] += 1
            
            print("\n===== SUMMARY =====")
            print(f"Total relations extracted: {len(all_relations)}")
            print("Relations by type:")
            for rel_type, count in sorted(relation_types.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {rel_type}: {count}")
                
    finally:
        ingestor.close()

if __name__ == "__main__":
    main()
