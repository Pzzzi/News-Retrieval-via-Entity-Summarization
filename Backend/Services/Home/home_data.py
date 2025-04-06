import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# ===== Database Connection Setup =====
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# ===== Homepage Data Functions =====
def get_recent_articles(limit=10):
    """Fetch most recent articles with optimized image selection"""
    pipeline = [
        {"$sort": {"date": -1}},
        {"$limit": limit},
        {"$project": {
            "title": 1,
            "url": 1,
            "date": 1,
            "_id": 1,
            "images": 1,
            "entities": {"$slice": ["$entities", 3]}  # Get first 3 entities
        }}
    ]
    
    articles = list(collection.aggregate(pipeline))

    def select_best_image(images):
        if not images:
            return None
            
        # Priority order for BBC images (adjust for your sources)
        resolutions = ['1536', '1024', '800', '640', '480']
        for res in resolutions:
            for img in images:
                if f"/{res}/" in img:
                    return img
        return images[0]

    return [{
        "_id": str(article["_id"]),
        "title": article["title"],
        "url": article["url"],
        "date": article["date"],
        "image": select_best_image(article.get("images")),
        "entities": [e["text"] for e in article.get("entities", [])]
    } for article in articles]

def get_popular_entities(limit=5):
    """Fetch most frequently mentioned entities"""
    pipeline = [
        {"$unwind": "$entities"},
        {"$group": {
            "_id": "$entities.text",
            "count": {"$sum": 1},
            "type": {"$first": "$entities.type"}
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
        {"$project": {
            "name": "$_id",
            "type": 1,
            "count": 1,
            "_id": 0
        }}
    ]
    
    return list(collection.aggregate(pipeline))

def get_homepage_data():
    """Combined endpoint for all homepage data"""
    return {
        "recent_articles": get_recent_articles(),
        "popular_entities": get_popular_entities()
    }