import os
import re
from pymongo import MongoClient
from neo4j import GraphDatabase
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

# ====== Database Connections ======
# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["test_articles"]

# Neo4j Connection
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def normalize_entity_name(entity_name):
    """Helper function to normalize entity names for comparison"""
    return entity_name.lower().strip()

# === Neo4j: Get Related Entities and Their Related Entities ===
def get_related_entities(entity_name):
    """Get entities related to the target entity and their second-degree relations"""
    normalized_name = normalize_entity_name(entity_name)
    query = """
    MATCH (e:Entity)
    WHERE toLower(e.name) = $normalized_name
    OPTIONAL MATCH (e)-[r:RELATION]-(related)
    OPTIONAL MATCH (related)-[r2:RELATION]-(related2)
    WHERE toLower(related2.name) <> $normalized_name
    RETURN DISTINCT 
        e.name AS main_entity_name,
        e.type AS main_entity_type,
        related.name AS related_name, 
        related.type AS related_type,
        COLLECT(DISTINCT {
            relation: r.type,
            confidence: r.confidence,
            sentence: r.sentence
        }) AS relations_to_main,
        related2.name AS related2_name, 
        related2.type AS related2_type,
        COLLECT(DISTINCT {
            relation: r2.type,
            confidence: r2.confidence,
            sentence: r2.sentence
        }) AS relations_between
    LIMIT 20
    """
    
    with driver.session() as session:
        result = session.run(query, normalized_name=normalized_name)
        
        nodes = {}
        links = []
        relation_details = defaultdict(list)
        main_entity = None

        for record in result:
            if not main_entity and record["main_entity_name"]:
                main_entity = {
                    "id": record["main_entity_name"],
                    "type": record["main_entity_type"],
                    "normalized_label": record["main_entity_name"]  # Using Neo4j stored name as normalized
                }
                nodes[normalize_entity_name(main_entity["id"])] = main_entity

            # First-degree relation (main entity to related)
            if record["related_name"]:
                related = {
                    "id": record["related_name"],
                    "type": record["related_type"],
                    "normalized_label": record["related_name"]  # Using Neo4j stored name as normalized
                }
                nodes[normalize_entity_name(related["id"])] = related
                
                # Add relation details
                for rel in record["relations_to_main"]:
                    relation_details[(normalize_entity_name(main_entity["id"]), normalize_entity_name(related["id"]))].append({
                        "type": rel["relation"],
                        "confidence": rel["confidence"],
                        "sentence": rel["sentence"]
                    })
                    links.append({
                        "source": main_entity["id"],
                        "target": related["id"],
                        "relation": rel["relation"],
                        "confidence": rel["confidence"]
                    })

            # Second-degree relation (related to related2)
            if record["related2_name"]:
                related2 = {
                    "id": record["related2_name"],
                    "type": record["related2_type"],
                    "normalized_label": record["related2_name"]  # Using Neo4j stored name as normalized
                }
                nodes[normalize_entity_name(related2["id"])] = related2
                
                for rel in record["relations_between"]:
                    relation_details[(normalize_entity_name(record["related_name"]), normalize_entity_name(related2["id"]))].append({
                        "type": rel["relation"],
                        "confidence": rel["confidence"],
                        "sentence": rel["sentence"]
                    })
                    links.append({
                        "source": record["related_name"],
                        "target": related2["id"],
                        "relation": rel["relation"],
                        "confidence": rel["confidence"]
                    })

        return {
            "nodes": list(nodes.values()),
            "links": links,
            "relation_details": {
                f"{src}||{tgt}": details
                for (src, tgt), details in relation_details.items()
            },
            "main_entity": main_entity or {"id": entity_name, "type": "UNKNOWN", "normalized_label": entity_name}
        }

# === MongoDB: Search Articles with Ranking ===
def search_articles_by_entity(entity_name, related_entities):
    """Fetch articles mentioning the entity & related entities, ranked by relevance."""
    # Create search terms including both raw and normalized versions
    search_terms = list({
        entity_name,
        *[e["id"] for e in related_entities],
        *[normalize_entity_name(e["id"]) for e in related_entities]
    })
    
    pipeline = [
        {"$match": {
            "$or": [
                {"entities.label": {"$in": search_terms}},
                {"entities.text": {"$in": search_terms}}
            ]
        }},
        {"$addFields": {
            "entity_match_score": {
                "$sum": [
                    # Exact match to the main entity (highest weight)
                    {"$size": {
                        "$filter": {
                            "input": "$entities",
                            "as": "ent",
                            "cond": {
                                "$or": [
                                    {"$eq": ["$$ent.label", entity_name]},
                                    {"$eq": ["$$ent.text", entity_name]}
                                ]
                            }
                        }
                    }},
                    # Partial matches to main entity (medium weight)
                    {"$multiply": [
                        0.7,
                        {"$size": {
                            "$filter": {
                                "input": "$entities",
                                "as": "ent",
                                "cond": {
                                    "$regexMatch": {
                                        "input": "$$ent.text",
                                        "regex": f".*{re.escape(entity_name)}.*",
                                        "options": "i"
                                    }
                                }
                            }
                        }}
                    ]},
                    # Matches to related entities (lower weight)
                    {"$multiply": [
                        0.5,
                        {"$size": {
                            "$filter": {
                                "input": "$entities",
                                "as": "ent",
                                "cond": {
                                    "$or": [
                                        {"$in": ["$$ent.label", search_terms[1:]]},
                                        {"$in": ["$$ent.text", search_terms[1:]]}
                                    ]
                                }
                            }
                        }}
                    ]}
                ]
            },
            # Add normalized entity information
            "matched_entities": {
                "$filter": {
                    "input": "$entities",
                    "as": "ent",
                    "cond": {
                        "$or": [
                            {"$in": ["$$ent.label", search_terms]},
                            {"$in": ["$$ent.text", search_terms]}
                        ]
                    }
                }
            }
        }},
        {"$sort": {"entity_match_score": -1, "date": -1}},
        {"$limit": 10},
        {"$project": {
            "title": 1,
            "url": 1,
            "date": 1,
            "_id": 1,
            "images": 1,
            "matched_entities": 1,
            "entity_match_score": 1
        }}
    ]
    
    articles = list(collection.aggregate(pipeline))

    def get_best_image(images):
        if not images:
            return None
        resolution_order = ['1536', '1586', '1526', '1024', '840', '800', '640', '480', '320', '240']
        for res in resolution_order:
            for img in images:
                if f"/{res}/" in img:
                    return img
        return images[0] if images else None

    processed_articles = []
    for article in articles:
        # Create a mapping of text->label for all entities in this article
        entity_normalization_map = {
            normalize_entity_name(ent["text"]): ent.get("label", ent["text"])
            for ent in article.get("entities", [])
        }
        
        # Process matched entities to use normalized labels
        normalized_matches = []
        for ent in article.get("matched_entities", []):
            normalized_label = ent.get("label", ent["text"])
            normalized_matches.append({
                "original_text": ent["text"],
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
            "matched_entities": normalized_matches,
            "match_score": article.get("entity_match_score", 0)
        })
    
    return processed_articles

# === Query Suggestion When No Results Are Found ===
def suggest_alternative_entities(entity_name):
    """Suggest similar entities when no results are found."""
    normalized_name = normalize_entity_name(entity_name)
    query = """
    MATCH (e:Entity)
    WHERE toLower(e.name) CONTAINS $normalized_name
    RETURN e.name AS name, e.type AS type
    ORDER BY 
        CASE WHEN toLower(e.name) STARTS WITH $normalized_name THEN 0 ELSE 1 END,
        size(e.name)
    LIMIT 5
    """
    with driver.session() as session:
        result = session.run(query, normalized_name=normalized_name)
        return [{
            "id": record["name"],
            "type": record["type"],
            "normalized_label": record["name"]  # Neo4j stores normalized names
        } for record in result]

# === Unified Search Function ===
def entity_search(entity_name):
    """Fetch related entities, ranked articles, and handle no-result cases."""
    normalized_name = normalize_entity_name(entity_name)
    related_data = get_related_entities(normalized_name)
    articles = search_articles_by_entity(normalized_name, related_data["nodes"])

    response = {
        "entity": related_data["main_entity"],
        "related_entities": related_data["nodes"],
        "links": related_data["links"],
        "relation_details": related_data["relation_details"],
        "articles": articles
    }

    if not articles:
        response["suggestions"] = suggest_alternative_entities(normalized_name)
    
    return response
