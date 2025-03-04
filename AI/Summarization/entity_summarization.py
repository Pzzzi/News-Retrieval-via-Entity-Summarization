import spacy
import nltk
from nltk.tokenize import sent_tokenize
from pymongo import MongoClient
from collections import Counter

# Download NLTK tokenizer if not already installed
nltk.download("punkt")

# Connect to MongoDB
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Load spaCy English NER model
nlp = spacy.load("en_core_web_sm")

def rank_entities(entities):
    """
    Rank entities based on:
    1. Frequency (how many times they appear)
    2. Type (assign higher weight to PERSON, ORG, GPE)
    """
    entity_counts = Counter([ent["text"] for ent in entities])
    entity_scores = {}

    # Assign higher weights to important entity types
    entity_weights = {"PERSON": 3, "ORG": 2, "GPE": 2, "DATE": 1, "EVENT": 1}

    for ent in entities:
        score = entity_counts[ent["text"]] * entity_weights.get(ent["label"], 1)
        entity_scores[ent["text"]] = score

    # Sort by score (higher = more important)
    ranked_entities = sorted(entity_scores.items(), key=lambda x: x[1], reverse=True)
    return [ent[0] for ent in ranked_entities[:5]]  # Top 5 entities

def summarize_article(article):
    """
    Generates a summary based on the most important entities.
    1. Rank entities
    2. Extract sentences containing top entities
    3. Rank sentences
    4. Return top sentences in original order
    """
    text = article.get("content", "")
    entities = article.get("entities", [])

    if not text or not entities:
        return None

    top_entities = rank_entities(entities)

    # Tokenize text into sentences
    sentences = sent_tokenize(text)

    # Score sentences based on entity mentions
    sentence_scores = []
    for sentence in sentences:
        score = sum(1 for ent in top_entities if ent in sentence)  # Count entity matches
        if score > 0:
            sentence_scores.append((sentence, score))

    # Sort sentences by score (higher = more important)
    sentence_scores.sort(key=lambda x: x[1], reverse=True)

    # Select top 3-5 sentences (adjustable)
    selected_sentences = [s[0] for s in sentence_scores[:5]]

    # Preserve original order
    summary = " ".join([s for s in sentences if s in selected_sentences])
    return summary

# Process each article
for article in collection.find():
    summary = summarize_article(article)

    if summary:
        collection.update_one(
            {"_id": article["_id"]},
            {"$set": {"summary": summary}}
        )
        print(f"✅ Summarized: {article['title']}\n📄 {summary}\n")

print("🎉 Entity-Based Summarization Complete!")

