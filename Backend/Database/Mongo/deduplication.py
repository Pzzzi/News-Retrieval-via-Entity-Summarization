from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["articles"]

def remove_title_based_duplicates():
    """Keep only the newest article for each title"""
    pipeline = [
        {"$sort": {"date": -1}},  # Newest first
        {"$group": {
            "_id": "$title",  # Group by title, not URL
            "latest_id": {"$first": "$_id"},
            "all_ids": {"$push": "$_id"},
            "count": {"$sum": 1}
        }},
        {"$match": {"count": {"$gt": 1}}}
    ]

    duplicates = list(collection.aggregate(pipeline))

    ids_to_delete = []
    for doc in duplicates:
        for _id in doc["all_ids"]:
            if _id != doc["latest_id"]:
                ids_to_delete.append(_id)

    if ids_to_delete:
        result = collection.delete_many({"_id": {"$in": ids_to_delete}})
        print(f"✅ Removed {result.deleted_count} duplicate articles (based on title)")
    else:
        print("✅ No duplicates found")

remove_title_based_duplicates()




