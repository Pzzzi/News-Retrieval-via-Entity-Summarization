from pymongo import MongoClient
from pprint import pprint
from dotenv import load_dotenv
import os

load_dotenv()

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["articles"]

def analyze_duplicates():
    """Run comprehensive duplicate analysis"""
    print("\n🔍 Starting duplicate analysis...")
    
    # 1. Basic duplicate count by URL
    pipeline = [
        {"$group": {
            "_id": "$url",
            "count": {"$sum": 1},
            "titles": {"$push": "$title"},
            "ids": {"$push": "$_id"},
            "latest_date": {"$max": "$date"},
            "earliest_date": {"$min": "$date"}
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    
    print("\n📊 Top 20 Most Duplicated URLs:")
    duplicates = list(collection.aggregate(pipeline))
    for dup in duplicates:
        print(f"\nURL: {dup['_id']}")
        print(f"Copies: {dup['count']}")
        print(f"Date Range: {dup['earliest_date']} to {dup['latest_date']}")
        print("Titles:")
        pprint(dup['titles'][:3])  # Show first 3 titles
    
    # 2. Sample duplicate documents for inspection
    if duplicates:
        sample_url = duplicates[0]['_id']
        print(f"\n🔎 Sample documents for '{sample_url[:50]}...':")
        sample_docs = list(collection.find({"url": sample_url}).limit(2))
        for i, doc in enumerate(sample_docs, 1):
            print(f"\n📄 Document {i}:")
            # Handle cases where images might be string or array
            image_count = 0
            if isinstance(doc.get("images"), list):
                image_count = len(doc["images"])
            elif doc.get("images"):  # If it's a string
                image_count = 1
            
            pprint({
                "_id": doc["_id"],
                "title": doc.get("title"),
                "date": doc.get("date"),
                "content_length": len(doc.get("content", "")),
                "image_count": image_count
            })
    
    # 3. Safer summary statistics (without $size on potentially non-array fields)
    stats_pipeline = [
        {"$group": {
            "_id": None,
            "total_articles": {"$sum": 1},
            "unique_urls": {"$addToSet": "$url"},
        }},
        {"$project": {
            "total_articles": 1,
            "unique_articles": {"$size": "$unique_urls"},
            "duplicate_percentage": {
                "$multiply": [
                    {"$divide": [
                        {"$subtract": ["$total_articles", {"$size": "$unique_urls"}]},
                        "$total_articles"
                    ]},
                    100
                ]
            }
        }}
    ]
    
    stats = list(collection.aggregate(stats_pipeline))[0]
    print("\n📈 Collection Summary:")
    print(f"Total articles: {stats['total_articles']}")
    print(f"Unique URLs: {stats['unique_articles']}")
    print(f"Duplicate percentage: {stats['duplicate_percentage']:.2f}%")

if __name__ == "__main__":
    analyze_duplicates()
    print("\n✅ Duplicate analysis complete")
