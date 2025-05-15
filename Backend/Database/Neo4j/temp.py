import os
import re
from pymongo import MongoClient
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from difflib import get_close_matches
import torch

# Minimal configuration
load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
db = client["news_db"]
collection = db["test_articles"]

# REBEL setup
tokenizer = AutoTokenizer.from_pretrained("Babelscape/rebel-large")
model = AutoModelForSeq2SeqLM.from_pretrained("Babelscape/rebel-large")

def get_rebel_triples(text):
    """Pure REBEL triple extraction with no side effects"""
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model.generate(
            inputs["input_ids"],
            max_length=512,
            num_beams=3,
            early_stopping=True
        )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=False)
    return re.findall(r"<triplet> (.*?) <subj> (.*?) <obj> (.*?)(?=<triplet>|</s>|$)", decoded)

def fuzzy_match(entity, db_entities, cutoff=0.6):
    """Fuzzy string matching to handle different surface forms"""
    matches = get_close_matches(entity, db_entities, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def analyze_article_improved(article):
    print(f"\n\033[1mArticle: {article.get('title', 'Untitled')}\033[0m")
    content = article.get("content", "")
    db_entities = {e["text"] for e in article.get("entities", [])}
    
    # REBEL extraction with better preprocessing
    sentences = [sent.strip() for sent in re.split(r'[.!?]', content) if sent.strip()]
    all_triples = []
    
    for sent in sentences:
        all_triples.extend(get_rebel_triples(sent))
    
    print(f"\nREBEL extracted {len(all_triples)} potential relations:")
    for s, p, o in all_triples:
        print(f"  {s[:30]:<30} → {p:<20} → {o[:30]}")
    
    # Improved entity matching
    valid = []
    for s, p, o in all_triples:
        s_matched = fuzzy_match(s, db_entities) or s
        o_matched = fuzzy_match(o, db_entities) or o
        if s_matched in db_entities and o_matched in db_entities:
            valid.append((s_matched, p, o_matched))
    
    print(f"\n\033[92m{len(valid)} validated relations:\033[0m")
    for s, p, o in valid:
        print(f"  {s:<30} → {p:<20} → {o}")

def run_clean_test(limit=5):
    """Run a completely clean read-only test"""
    print("\033[1m\033[94m=== REBEL Evaluation (Read-Only) ===\033[0m")
    for article in collection.find({"entities": {"$exists": True}}).limit(limit):
        analyze_article_improved(article)
    print("\n\033[92mEvaluation complete - database unchanged\033[0m")

if __name__ == "__main__":
    try:
        run_clean_test()
    finally:
        client.close()  # Clean connection handling
