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
collection = db["articles"]

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
    """Get entities related to the target entity with improved relationship filtering"""
    normalized_name = normalize_entity_name(entity_name)
    
    # Improved query with relationship filtering and limits
    query = """
    MATCH (e:Entity)
    WHERE toLower(e.name) = $normalized_name
    WITH e
    OPTIONAL MATCH (e)-[r:RELATION]-(related)
    WHERE r.confidence > 0.7  // Lowered confidence threshold
    WITH e, related, r
    ORDER BY r.confidence DESC
    LIMIT 20  // Increased limit for main entity relationships
    WITH e, collect({related: related, r: r}) AS relatedRelations

    UNWIND relatedRelations AS rr
    WITH e, rr.related AS related, rr.r AS r
    OPTIONAL MATCH (related)-[r2:RELATION]-(related2)
    WHERE toLower(related2.name) <> $normalized_name
    AND r2.confidence > 0.7  // Lowered confidence threshold
    WITH e, related, r, related2, r2
    ORDER BY r2.confidence DESC
    WITH e, related, r, collect({related2: related2, r2: r2})[0..5] AS secondDegreeRelations

    UNWIND secondDegreeRelations AS sdr
    RETURN DISTINCT 
        e.name AS main_entity_name,
        e.type AS main_entity_type,
        related.name AS related_name, 
        related.type AS related_type,
        r.type AS relation_to_main,
        r.confidence AS confidence_to_main,
        r.sentence AS sentence_to_main,
        sdr.related2.name AS related2_name, 
        sdr.related2.type AS related2_type,
        sdr.r2.type AS relation_between,
        sdr.r2.confidence AS confidence_between,
        sdr.r2.sentence AS sentence_between
    """
    
    with driver.session() as session:
        result = session.run(query, normalized_name=normalized_name)
        
        nodes = {}
        links = []
        relation_details = defaultdict(list)
        main_entity = None
        seen_relationships = set()  # Track seen relationships to avoid duplicates

        for record in result:
            if not main_entity and record["main_entity_name"]:
                main_entity = {
                    "id": record["main_entity_name"],
                    "type": record["main_entity_type"],
                    "normalized_label": record["main_entity_name"]
                }
                nodes[normalize_entity_name(main_entity["id"])] = main_entity

            # First-degree relation processing
            if record["related_name"]:
                related = {
                    "id": record["related_name"],
                    "type": record["related_type"],
                    "normalized_label": record["related_name"]
                }
                nodes[normalize_entity_name(related["id"])] = related
                
                # Create relationship key to check for duplicates
                rel_key = (main_entity["id"], related["id"], record["relation_to_main"])
                
                if rel_key not in seen_relationships:
                    seen_relationships.add(rel_key)
                    relation_details[(normalize_entity_name(main_entity["id"]), 
                                    normalize_entity_name(related["id"]))].append({
                        "type": record["relation_to_main"],
                        "confidence": record["confidence_to_main"],
                        "sentence": record["sentence_to_main"]
                    })
                    
                    links.append({
                        "source": main_entity["id"],
                        "target": related["id"],
                        "relation": record["relation_to_main"],
                        "confidence": record["confidence_to_main"],
                        "is_direct": True  # Mark as direct relationship
                    })

            # Second-degree relation processing
            if record["related2_name"]:
                related2 = {
                    "id": record["related2_name"],
                    "type": record["related2_type"],
                    "normalized_label": record["related2_name"]
                }
                nodes[normalize_entity_name(related2["id"])] = related2
                
                rel_key = (record["related_name"], related2["id"], record["relation_between"])
                
                if rel_key not in seen_relationships:
                    seen_relationships.add(rel_key)
                    relation_details[(normalize_entity_name(record["related_name"]), 
                                    normalize_entity_name(related2["id"]))].append({
                        "type": record["relation_between"],
                        "confidence": record["confidence_between"],
                        "sentence": record["sentence_between"]
                    })
                    
                    links.append({
                        "source": record["related_name"],
                        "target": related2["id"],
                        "relation": record["relation_between"],
                        "confidence": record["confidence_between"],
                        "is_direct": False  # Mark as indirect relationship
                    })

        # Post-process links to improve visualization quality
        processed_links = []
        link_counts = defaultdict(int)

    # First pass - count connections but don't filter main entity connections
    for link in links:
        if link["source"] != main_entity["id"] and link["target"] != main_entity["id"]:
                link_counts[link["source"]] += 1
                link_counts[link["target"]] += 1

        # Second pass - filter but always keep main entity connections
        for link in links:
            # Always keep connections to main entity
            if link["source"] == main_entity["id"] or link["target"] == main_entity["id"]:
                processed_links.append({
                    **link,
                    "score": link["confidence"] * 1.5  # Boost score for main entity connections
                })
                continue
        
            # For other links, apply filtering
            if link_counts.get(link["source"], 0) > 10 or link_counts.get(link["target"], 0) > 10:
                continue
        
            score = link["confidence"]
            if any(d["sentence"] == link.get("sentence", "") for d in relation_details.get(
                f"{link['source']}||{link['target']}", [])):
                score *= 0.7
                
            processed_links.append({
                **link,
                "score": score
            })
        
        # Sort by score and take top relationships
        processed_links.sort(key=lambda x: -x["score"])
        processed_links = processed_links[:50]  # Limit to top 50 relationships

        return {
            "nodes": list(nodes.values()),
            "links": [link for link in processed_links if link["score"] > 0.5],  # Lowered threshold
            "relation_details": {
                f"{src}||{tgt}": details
                for (src, tgt), details in relation_details.items()
            },
            "main_entity": main_entity or {
                "id": entity_name, 
                "type": "UNKNOWN", 
                "normalized_label": entity_name
            }
        }

# === MongoDB: Search Articles with Ranking ===
def search_articles_by_entity(entity_name, related_entities, page=1, per_page=10):
    """Fetch articles mentioning the entity & related entities, ranked by relevance."""
    search_terms = list({
        entity_name,
        *[e["id"] for e in related_entities],
        *[normalize_entity_name(e["id"]) for e in related_entities]
    })
    
    skip = (page - 1) * per_page
    
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
        {"$skip": skip},
        {"$limit": per_page},
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
    
    # Also get total count for pagination
    count_pipeline = [
        {"$match": {
            "$or": [
                {"entities.label": {"$in": search_terms}},
                {"entities.text": {"$in": search_terms}}
            ]
        }},
        {"$count": "total"}
    ]
    
    articles = list(collection.aggregate(pipeline))
    total_count = list(collection.aggregate(count_pipeline))
    total = total_count[0]["total"] if total_count else 0
    
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
    
    return {
        "articles": processed_articles,
        "total": total,
        "page": page,
        "per_page": per_page,
        "has_more": skip + per_page < total
    }

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
def entity_search(entity_name, page=1, per_page=10):
    """Fetch related entities, ranked articles, and handle no-result cases."""
    normalized_name = normalize_entity_name(entity_name)
    related_data = get_related_entities(normalized_name)
    article_data = search_articles_by_entity(normalized_name, related_data["nodes"], page, per_page)

    response = {
        "entity": related_data["main_entity"],
        "related_entities": related_data["nodes"],
        "links": related_data["links"],
        "relation_details": related_data["relation_details"],
        "articles": article_data["articles"],
        "pagination": {
            "total": article_data["total"],
            "page": article_data["page"],
            "per_page": article_data["per_page"],
            "has_more": article_data["has_more"]
        }
    }

    if not article_data["articles"]:
        response["suggestions"] = suggest_alternative_entities(normalized_name)
    
    return response
