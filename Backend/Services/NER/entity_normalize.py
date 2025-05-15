import spacy
from spacy_entity_linker import EntityLinker

# Initialize pipeline
nlp = spacy.load("en_core_web_sm")
nlp.add_pipe("entityLinker", last=True)

def extract_linked_entities(text):
    doc = nlp(text)
    entities = []

    for linked_ent in doc._.linkedEntities:
        linker_span = linked_ent.get_span()
        
        # 1. First try exact character offset matching (strict)
        matching_ner = next(
            (ent for ent in doc.ents if ent.start_char == linker_span.start_char and ent.end_char == linker_span.end_char),
            None
        )
        
        # 2. Fallback: Match by text (flexible) if offsets don't align
        if matching_ner is None:
            matching_ner = next(
                (ent for ent in doc.ents if linker_span.text.lower() in ent.text.lower()),
                None
            )

        entities.append({
            "text": linker_span.text,
            "type": matching_ner.label_ if matching_ner else "UNKNOWN",
            "wikidata_id": linked_ent.get_id(),
            "wikidata_url": linked_ent.get_url(),
            "description": linked_ent.get_description(),
            "label": linked_ent.get_label()
        })

    return entities

# Example usage
text = "Apple is competing with Microsoft in the United States"
results = extract_linked_entities(text)

for ent in results:
    print(f"Entity: {ent['text']}")
    print(f"Type: {ent['type']}")
    print(f"Wikidata ID: {ent['wikidata_id']}")
    print(f"URL: {ent['wikidata_url']}")
    print(f"Description: {ent['description'][:100]}...")
    print("---")
   