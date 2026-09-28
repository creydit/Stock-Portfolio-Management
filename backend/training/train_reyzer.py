
from pathlib import Path

import joblib
from datasets import load_dataset, concatenate_datasets
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report


# --------------------------------------------------
# 1. Project paths
# --------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = BACKEND_DIR / "saved_models"

MODEL_DIR.mkdir(parents=True, exist_ok=True)


# --------------------------------------------------
# 2. Load Financial PhraseBank
# --------------------------------------------------

print("Loading complete Financial PhraseBank dataset...")

dataset_dict = load_dataset(
    "gtfintechlab/financial_phrasebank_sentences_allagree",
    "5768"
)

dataset = concatenate_datasets(
    [split for split in dataset_dict.values()]
)

print("\nCombined dataset:")
print(dataset)
print("Total samples:", len(dataset))


# --------------------------------------------------
# 3. Extract sentences and convert labels
# --------------------------------------------------

texts = dataset["sentence"]
raw_labels = dataset["label"]

label_feature = dataset.features["label"]

if hasattr(label_feature, "names") and label_feature.names:
    label_names = label_feature.names
    labels = [label_names[int(label)] for label in raw_labels]
else:
    labels = [str(label) for label in raw_labels]

labels = [label.strip().lower() for label in labels]

label_mapping = {
    "0": "negative",
    "1": "neutral",
    "2": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "positive": "positive",
}

labels = [label_mapping.get(label, label) for label in labels]

expected_labels = {"negative", "neutral", "positive"}

if set(labels) != expected_labels:
    raise ValueError(
        f"Unexpected labels found: {set(labels)}"
    )

print("\nOriginal label distribution:")

for label in sorted(set(labels)):
    print(f"{label}: {labels.count(label)}")


# --------------------------------------------------
# 4. Convert the dataset to binary classification
# --------------------------------------------------

print("\nRemoving neutral examples...")

binary_data = [
    (text, label)
    for text, label in zip(texts, labels)
    if label in ["negative", "positive"]
]

texts = [text for text, label in binary_data]
labels = [label for text, label in binary_data]

print("\nBinary dataset distribution:")

for label in ["negative", "positive"]:
    print(f"{label}: {labels.count(label)}")

print("Total binary samples:", len(texts))


# --------------------------------------------------
# 5. Create stratified 80/20 train/test split
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    texts,
    labels,
    test_size=0.2,
    random_state=42,
    stratify=labels,
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# --------------------------------------------------
# 6. TF-IDF feature extraction
# --------------------------------------------------

print("\nFitting TF-IDF vectorizer...")

vectorizer = TfidfVectorizer(
    ngram_range=(1, 2),
    max_features=5000,
    stop_words="english",
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

print("Training feature matrix:", X_train_tfidf.shape)
print("Testing feature matrix:", X_test_tfidf.shape)


# --------------------------------------------------
# 7. Train binary Logistic Regression
# --------------------------------------------------

print("\nTraining binary ReyZer Logistic Regression...")

model = LogisticRegression(
    C=1.0,
    class_weight="balanced",
    max_iter=1000,
    random_state=42,
)

model.fit(X_train_tfidf, y_train)


# --------------------------------------------------
# 8. Evaluate on held-out test data
# --------------------------------------------------

print("\nEvaluating model...")

predictions = model.predict(X_test_tfidf)

accuracy = accuracy_score(y_test, predictions)

print(f"\ntest accuracy: {accuracy:.4f}")

print("\nClassification report:")

print(
    classification_report(
        y_test,
        predictions,
        labels=["negative", "positive"],
        zero_division=0,
    )
)


# --------------------------------------------------
# 9. Save as the MAIN ReyZer model
# --------------------------------------------------

model_path = MODEL_DIR / "reyzer_model.joblib"
vectorizer_path = MODEL_DIR / "reyzer_vectorizer.joblib"

joblib.dump(model, model_path)
joblib.dump(vectorizer, vectorizer_path)

print("\n ReyZer training completed successfully!")

print("Model saved to:", model_path)
print("Vectorizer saved to:", vectorizer_path)