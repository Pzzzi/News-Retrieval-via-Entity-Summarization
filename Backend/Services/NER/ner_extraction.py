import spacy
from spacy_entity_linker import EntityLinker
from pymongo import MongoClient, UpdateMany
from tqdm import tqdm
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize NLP pipeline
nlp = spacy.load("en_core_web_trf")
nlp.add_pipe("entityLinker", last=True)

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["test_articles"]

# Entity types to exclude
EXCLUDED_TYPES = {"CARDINAL", "DATE", "PRODUCT"}

def extract_filtered_entities(text):
    """Extract entities with valid NER labels and Wikidata linking"""
    doc = nlp(text)
    entities = []
    seen_texts = set()

    for linked_ent in doc._.linkedEntities:
        span = linked_ent.get_span()

        if span.text.lower() in seen_texts:
            continue
        seen_texts.add(span.text.lower())

        matching_ner = next(
            (ent for ent in doc.ents 
             if ent.start == span.start and ent.end == span.end and ent.label_ not in EXCLUDED_TYPES),
            None
        )

        if matching_ner:
            entities.append({
                "text": span.text,
                "type": matching_ner.label_,
                "wikidata_id": linked_ent.get_id(),
                "wikidata_url": linked_ent.get_url(),
                "description": linked_ent.get_description(),
                "label": linked_ent.get_label()
            })

    return entities

def process_collection():
    """Process articles in MongoDB and attach entity information"""
    query = {"entities": {"$exists": False}, "content": {"$exists": True, "$ne": ""}}
    total = collection.count_documents(query)

    with tqdm(total=total, desc="Processing Articles") as pbar:
        batch_size = 200
        for i in range(0, total, batch_size):
            batch = list(collection.find(query).skip(i).limit(batch_size))
            if not batch:
                break

            texts = [doc["content"] for doc in batch]
            docs = nlp.pipe(texts, batch_size=8)  # Smaller batch due to transformer memory use

            updates = []
            for doc, article in zip(docs, batch):
                entities = extract_filtered_entities(doc.text)
                if entities:
                    updates.append(
                        UpdateMany(
                            {"_id": article["_id"]},
                            {"$set": {"entities": entities}}
                        )
                    )
                pbar.update(1)

            if updates:
                collection.bulk_write(updates, ordered=False)

if __name__ == "__main__":
    process_collection()
    print("✅ Processing complete!")





