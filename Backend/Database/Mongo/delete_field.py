from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["test_articles"]

# Remove the "entities" field from all documents
result = collection.update_many(
    {},  # Empty filter matches all documents
    {"$unset": {"entities": ""}}  # $unset removes the field
)

print(f"Removed 'entities' field from {result.modified_count} documents in 'test_articles' collection")
