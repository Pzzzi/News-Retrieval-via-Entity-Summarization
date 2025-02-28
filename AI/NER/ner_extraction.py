import spacy
from pymongo import MongoClient

# Connect to MongoDB
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Load spaCy English NER model
nlp = spacy.load("en_core_web_sm")

# Process each article
for article in collection.find():
    text = article.get("content", "")

    if text:
        doc = nlp(text)

        # Extract entities
        entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]

        # Update MongoDB with extracted entities
        collection.update_one(
            {"_id": article["_id"]},
            {"$set": {"entities": entities}}
        )

        print(f"✅ Processed: {article['title']} - Found {len(entities)} entities")

print("🎉 NER Extraction Complete!")
