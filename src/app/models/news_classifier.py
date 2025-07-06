# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.linear_model import LogisticRegression
# from sklearn.pipeline import Pipeline
# from datasets import load_dataset, load_from_disk
import os
import joblib


# dataset = load_from_disk(os.path.join(
#     os.path.dirname(__file__), "ag_news_train"))
# texts = dataset["text"]
# label_indices = dataset["label"]
# label_names = dataset.features["label"].names
# labels = [label_names[i] for i in label_indices]

# pipeline = Pipeline([
#     ("vectorizer", TfidfVectorizer(max_features=3000)),
#     ("classifier", LogisticRegression(max_iter=300))
# ])

# pipeline.fit(texts, labels)


model_path = os.path.join(os.path.dirname(__file__), "ag_news_classifier.pkl")
# joblib.dump(pipeline, model_path)       # Save
model = joblib.load(model_path)         # Load

# Save model


def classify_articles(texts: list) -> list:
    predictions = model.predict(texts)
    return predictions
    # for text, category in zip(texts, predictions):
    #     print(f"Text: {text}\nPredicted category: {category}\n")


x = [
    "Ronaldo just scored the finishing against AC milan today",
    "Microsoft just released thier newest model",
    "I know how to dance",
    "The US is interviening in the war between the iran and isreal"
]

# classify_articles(x)
# Output: 'Sci/Tech'


# dataset = load_dataset("ag_news", split="train")
# dataset.save_to_disk(os.path.join(os.path.dirname(__file__), "ag_news_train"))
# dataset = load_from_disk(os.path.join(
#     os.path.dirname(__file__), "ag_news_train"))
# texts = dataset["text"]
# labels = dataset["label"]
# label_names = dataset.features["label"].names

# print(f"First sample: {texts[0]} → {label_names[labels[0]]}")
# labels = dataset.features["label"].names
# print(labels)
