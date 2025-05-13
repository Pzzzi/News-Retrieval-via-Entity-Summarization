from datasets import load_dataset
from pathlib import Path
import spacy
from spacy.tokens import DocBin

nlp = spacy.blank("en")

def convert_split(split, output_path):
    doc_bin = DocBin()
    for item in split:
        words = item["tokens"]
        tags = item["ner_tags"]
        doc = nlp.make_doc(" ".join(words))

        ents = []
        start = 0
        for word, tag in zip(words, tags):
            start_char = doc.text.find(word, start)
            end_char = start_char + len(word)
            start = end_char

            tag_label = split.features["ner_tags"].feature.names[tag]
            if tag_label != "O":
                if tag_label.startswith("B-"):
                    ents.append(spacy.tokens.Span(doc, doc.char_span(start_char, end_char).start, doc.char_span(start_char, end_char).end, label=tag_label[2:]))

        doc.ents = ents
        doc_bin.add(doc)
    doc_bin.to_disk(output_path)

# Load and convert with trust_remote_code
dataset = load_dataset("conll2003", trust_remote_code=True)
convert_split(dataset["train"], "train.spacy")
convert_split(dataset["validation"], "dev.spacy")
convert_split(dataset["test"], "test.spacy")

