import spacy
import re

# Load spaCy English NER model
nlp = spacy.load("en_core_web_sm")

# Define unwanted labels for filtering
UNWANTED_LABELS = {"CARDINAL", "ORDINAL", "QUANTITY", "PERCENT", "MONEY", "TIME", "DATE"}

# Sample test articles
test_articles = [
    {
        "title": "Trump speaks in New York",
        "content": "Donald Trump gave a speech in New York on Tuesday. He said the economy is booming with a $350bn budget. Donald Trump's, he is free."
    },
    {
        "title": "Numbers in the news",
        "content": "123 people attended. First responders were present. Total cost: $2 million. It happened on January 5th."
    },
    {
        "title": "Mixed Entities",
        "content": "Apple's CEO Tim Cook visited the White House. Apple's shares rose by 3%."
    }
]

# --- Cleaning Functions ---

def filter_entities(entities):
    """Filter out noisy/unwanted entities."""
    return [
        ent for ent in entities
        if ent["label"] not in UNWANTED_LABELS
        and not ent["text"].strip().isdigit()
        and len(ent["text"].strip()) > 2
    ]

def normalize_text(text):
    """Normalize entity text."""
    text = text.lower().strip()
    text = re.sub(r"'s\b", "", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.title()

def deduplicate_entities(entities):
    """Remove duplicates after normalization."""
    seen = set()
    cleaned = []
    for ent in entities:
        norm_text = normalize_text(ent["text"])
        key = (norm_text, ent["label"])
        if key not in seen:
            seen.add(key)
            cleaned.append({"text": norm_text, "label": ent["label"]})
    return cleaned

def clean_entities(raw_entities):
    """Complete filter + normalize + deduplicate pipeline."""
    filtered = filter_entities(raw_entities)
    cleaned = deduplicate_entities(filtered)
    return cleaned

# --- Run Test ---

for article in test_articles:
    text = article["content"]
    doc = nlp(text)
    raw_entities = [{"text": ent.text, "label": ent.label_} for ent in doc.ents]
    cleaned_entities = clean_entities(raw_entities)

    print(f"\n📰 Title: {article['title']}")
    print("🔍 Raw Entities:")
    for ent in raw_entities:
        print(f"   - {ent}")
    print("✅ Cleaned Entities:")
    for ent in cleaned_entities:
        print(f"   - {ent}")


