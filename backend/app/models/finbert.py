import os

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
)

MODEL_NAME = "ProsusAI/finbert"

# Set SENTOCK_DEVICE=cpu on cloud servers if needed.
# "auto" selects GPU when available, otherwise CPU.
DEVICE_SETTING = os.getenv("SENTOCK_DEVICE", "auto").lower()

if DEVICE_SETTING == "auto":
    DEVICE = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )
elif DEVICE_SETTING == "cpu":
    DEVICE = torch.device("cpu")
elif DEVICE_SETTING == "cuda":
    if not torch.cuda.is_available():
        raise RuntimeError(
            "SENTOCK_DEVICE=cuda was set, "
            "but CUDA is not available."
        )
    DEVICE = torch.device("cuda")
else:
    raise ValueError(
        "SENTOCK_DEVICE must be 'auto', 'cpu', or 'cuda'."
    )

print(f"Loading FinBERT on {DEVICE}...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME
)

model.to(DEVICE)
model.eval()

LABELS = model.config.id2label


def analyze_sentiment(headlines, batch_size=8):
    results = []

    if not headlines:
        return results

    if batch_size < 1:
        raise ValueError("batch_size must be at least 1.")

    for start in range(0, len(headlines), batch_size):
        batch = headlines[start:start + batch_size]

        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(DEVICE)
            for key, value in inputs.items()
        }

        # Optimized inference without gradient tracking.
        with torch.inference_mode():
            outputs = model(**inputs)

            probabilities = torch.softmax(
                outputs.logits,
                dim=1,
            )

        for probs in probabilities:
            scores = {
                LABELS[i].lower(): probs[i].item()
                for i in range(len(LABELS))
            }

            positive = scores.get("positive", 0.0)
            negative = scores.get("negative", 0.0)
            neutral = scores.get("neutral", 0.0)

            sentiment = max(
                scores,
                key=scores.get,
            )

            results.append({
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "sentiment": sentiment,
                "sentiment_score": positive - negative,
            })

    return results