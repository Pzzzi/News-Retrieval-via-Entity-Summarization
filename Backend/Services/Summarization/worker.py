import os
from datasets import load_dataset
from transformers import (
    T5TokenizerFast,
    T5ForConditionalGeneration,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
)
import evaluate

dataset = load_dataset("cnn_dailymail", "3.0.0", cache_dir="D:/FYP SUMMARIZATION/DATASET")

model_name = "t5-small"
tokenizer = T5TokenizerFast.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

def preprocess(example):
    # Ensure 'article' and 'highlights' are strings
    inputs = tokenizer(
        example["article"],
        max_length=1024,
        truncation=True,
        padding="max_length"
    )
    
    # Convert to strings if needed (especially for batch mode)
    targets_texts = example["highlights"]
    if isinstance(targets_texts, list):
        targets_texts = [str(t) if t is not None else "" for t in targets_texts]
    else:
        targets_texts = str(targets_texts) if targets_texts is not None else ""
    
    with tokenizer.as_target_tokenizer():
        targets = tokenizer(
            targets_texts,
            max_length=128,
            truncation=True,
            padding="max_length"
        )

    inputs["labels"] = targets["input_ids"]
    return inputs

tokenized_datasets = dataset.map(preprocess, batched=True, remove_columns=["article", "highlights", "id"])

data_collator = DataCollatorForSeq2Seq(tokenizer, model=model)
rouge = evaluate.load("rouge")

def compute_metrics(eval_preds):
    preds, labels = eval_preds
    decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    return rouge.compute(predictions=decoded_preds, references=decoded_labels, use_stemmer=True)

training_args = Seq2SeqTrainingArguments(
    output_dir="D:/FYP SUMMARIZATION/MODEL",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=1,
    predict_with_generate=True,
    evaluation_strategy="epoch",
    save_total_limit=2,
    learning_rate=2e-5,
    weight_decay=0.01,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"].shuffle(seed=42).select(range(20000)),
    eval_dataset=tokenized_datasets["validation"].select(range(5000)),  # smaller eval subset for speed
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

trainer.train()


