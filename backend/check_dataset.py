
from datasets import load_dataset
from collections import Counter

data = load_dataset(
    "gtfintechlab/financial_phrasebank_sentences_allagree",
    "5768"
)

for split_name, split in data.items():
    feature = split.features["label"]
    labels = split["label"]

    if hasattr(feature, "names") and feature.names:
        labels = [feature.names[int(x)] for x in labels]

    print(f"\n{split_name}: {len(split)} samples")
    print(Counter(labels))