import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

load_dotenv()

# ====== MongoDB Connection ======
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

def suggest_entities(query):
    if not query:
        return []

    regex = {"$regex": query, "$options": "i"}
    pipeline = [
        {"$unwind": "$entities"},
        {"$match": {"entities.text": regex}},
        {"$group": {
            "_id": "$entities.text",
            "type": {"$first": "$entities.label"}
        }},
        {"$sort": {"_id": 1}},
        {"$limit": 10},
        {"$project": {
            "text": "$_id",
            "type": "$type",
            "_id": 0
        }}
    ]

    suggestions = list(collection.aggregate(pipeline))
    print(f"Suggestions for '{query}':", suggestions)
    return suggestions

