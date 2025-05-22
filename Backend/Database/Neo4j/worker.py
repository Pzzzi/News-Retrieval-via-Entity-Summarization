import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding,
)
from sklearn.metrics import accuracy_score, f1_score
import numpy as np
import os

# Set custom output path
output_dir = "D:/FYP RELATION CLASSIFIER MODEL ROBERTA"
os.makedirs(output_dir, exist_ok=True)

# 1. Load dataset
dataset = load_dataset("joelniklaus/sem_eval_2010_task_8")

# 2. Label mappings
labels = dataset["train"].features["relation"].names
label2id = {label: idx for idx, label in enumerate(labels)}
id2label = {idx: label for idx, label in enumerate(labels)}
num_labels = len(label2id)

# 3. Load tokenizer and model
model_checkpoint = "roberta-base"
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
model = AutoModelForSequenceClassification.from_pretrained(
    model_checkpoint,
    num_labels=num_labels,
    id2label=label2id,
    label2id=id2label
)

# 4. Preprocessing
def preprocess(example):
    tokenized = tokenizer(example["sentence"], truncation=True)
    tokenized["label"] = example["relation"]  # Add this line
    return tokenized

tokenized_dataset = dataset.map(preprocess, batched=True)
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# 5. Metrics
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    acc = accuracy_score(labels, predictions)
    f1 = f1_score(labels, predictions, average="macro")
    return {"accuracy": acc, "f1": f1}

# 6. Training arguments
training_args = TrainingArguments(
    output_dir=output_dir,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=5,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model="f1",
    logging_dir=os.path.join(output_dir, "logs"),
    logging_steps=10,
)

# 7. Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

# 8. Train!
trainer.train()

# 9. Save final model + tokenizer
trainer.save_model(output_dir)
tokenizer.save_pretrained(output_dir)







