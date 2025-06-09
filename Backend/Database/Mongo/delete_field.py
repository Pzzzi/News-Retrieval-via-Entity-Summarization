from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["articles"]

# Remove the "neo4j_processed" field from all documents
result = collection.update_many(
    {},  # Empty filter matches all documents
    {"$unset": {"neo4j_processed": ""}}  # $unset removes the field
)

print(f"Removed 'neo4j_processed' field from {result.modified_count} documents in 'test_articles' collection")
