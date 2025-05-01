from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]

# Delete all documents with Guardian URLs
result = db.articles.delete_many({
    "url": {"$regex": "^https://www.theguardian.com/"}
})

print(f"Deleted {result.deleted_count} documents from 'articles' collection")
