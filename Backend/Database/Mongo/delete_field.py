import os 
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URI=os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Field to remove
field_to_remove = "summary"  # Change this to the field you want to delete

# Update all documents to remove the field
result = collection.update_many({}, {"$unset": {field_to_remove: ""}})

print(f"✅ {result.modified_count} documents updated. '{field_to_remove}' field removed.")
