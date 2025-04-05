# from pymongo import MongoClient
# from bson.objectid import ObjectId
# import time
# from Services.NER.ner_extraction import extract_entities  # Import your NER function
# from Database.Neo4j.neo4j_ingestion import insert_entities_into_neo4j  # Import your Neo4j function

# client = MongoClient(MONGO_URI)
# db = client[DB_NAME]
# collection = db[COLLECTION_NAME]

# # === Change Stream Listener ===
# def process_new_article(article):
#     """Process a new article: Extract entities and insert into Neo4j"""
#     article_id = str(article["_id"])
#     title = article.get("title", "")
#     content = article.get("content", "")

#     print(f"📌 New article detected: {title}")

#     # 1️⃣ Extract Entities using NER
#     entities = extract_entities(content)

#     # 2️⃣ Insert Entities & Relationships into Neo4j
#     insert_entities_into_neo4j(entities, article_id)

#     print(f"✅ Processed: {title}")

# def watch_collection():
#     """Listen for new articles and process them"""
#     print("👀 Watching MongoDB for new articles...")

#     with collection.watch() as stream:
#         for change in stream:
#             if change["operationType"] == "insert":
#                 new_article = change["fullDocument"]
#                 process_new_article(new_article)

# if __name__ == "__main__":
#     while True:
#         try:
#             watch_collection()
#         except Exception as e:
#             print(f"⚠️ Error: {e}")
#             time.sleep(5)  # Wait before retrying
