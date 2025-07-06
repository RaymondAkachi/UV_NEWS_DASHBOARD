from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text):
    score = analyzer.polarity_scores(text)
    return score["compound"]  # Main value for plotting


if __name__ == "__main__":
    print(analyze_sentiment(
        "Everyone in the world is sad"))
