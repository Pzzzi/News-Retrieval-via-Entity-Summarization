from pymongo import MongoClient, ASCENDING
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
collection = client["news_db"]["test_articles"]

collection.create_index([("entities", ASCENDING)])
collection.create_index([("content", ASCENDING)])
print("Indexes created.")
