from pymongo import MongoClient
from pprint import pprint
from dotenv import load_dotenv
import os

load_dotenv()

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["articles"]

def remove_duplicates():
    """Keep only the newest version of each article"""
    pipeline = [
        {"$sort": {"date": -1}},  # Newest first
        {"$group": {
            "_id": "$url",
            "unique_ids": {"$first": "$_id"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]
    
    duplicates = list(collection.aggregate(pipeline))
    ids_to_keep = [d["unique_ids"] for d in duplicates]
    
    result = collection.delete_many({
        "url": {"$in": [d["_id"] for d in duplicates]},
        "_id": {"$nin": ids_to_keep}
    })
    
    print(f"✅ Removed {result.deleted_count} duplicates")

remove_duplicates()



