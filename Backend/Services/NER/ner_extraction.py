import spacy
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Load spaCy English NER model
nlp = spacy.load("en_core_web_sm")

# Process only articles without entities
for article in collection.find({"entities": {"$exists": False}}):  
    text = article.get("content", "")

    if text.strip():
        doc = nlp(text)
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

        collection.update_one(
            {"_id": article["_id"]},
            {"$set": {"entities": entities}}
        )

        print(f"✅ Processed: {article['title']} - Found {len(entities)} entities")

print("🎉 NER Extraction Complete!")

