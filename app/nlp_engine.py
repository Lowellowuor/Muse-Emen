import logging
from abc import ABC, abstractmethod
from sklearn.feature_extraction.text import CountVectorizer
import os

logger = logging.getLogger(__name__)

class InsightResult:
    def __init__(self, themes: list, sentiment_score: float, keywords: list):
        self.themes = themes
        self.sentiment_score = sentiment_score
        self.keywords = keywords

class NLPEngine(ABC):
    @abstractmethod
    def analyze(self, raw_text: str) -> InsightResult:
        pass

class FallbackNLPEngine(NLPEngine):
    def __init__(self):
        self.nlp = None
        self.vectorizer = None

    def _initialize(self):
        if self.nlp is None:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        if self.vectorizer is None:
            self.vectorizer = CountVectorizer(stop_words='english', max_features=5)

    def analyze(self, raw_text: str) -> InsightResult:
        self._initialize()
        try:
            X = self.vectorizer.fit_transform([raw_text])
            terms = self.vectorizer.get_feature_names_out()
            scores = X.toarray()[0]
            top_indices = scores.argsort()[-3:][::-1]
            themes = [terms[i] for i in top_indices if scores[i] > 0]
            if not themes:
                themes = ["reflection"]

            from textblob import TextBlob
            sentiment = TextBlob(raw_text).sentiment.polarity

            return InsightResult(
                themes=themes,
                sentiment_score=round(sentiment, 2),
                keywords=themes
            )
        except Exception as e:
            logger.error(f"NLP fallback failed: {e}")
            return InsightResult(themes=["unclassified"], sentiment_score=0.0, keywords=["general"])

class OpenAIMockEngine(NLPEngine):
    def analyze(self, raw_text: str) -> InsightResult:
        return InsightResult(
            themes=["dynamic-ai-theme-1", "dynamic-ai-theme-2"],
            sentiment_score=0.75,
            keywords=["future", "intelligence", "human"]
        )

class NLPEngineFactory:
    @classmethod
    def get_engine(cls) -> NLPEngine:
        engine_type = os.getenv("NLP_ENGINE_TYPE", "fallback").lower()
        if engine_type == "openai" or engine_type == "ollama":
            return OpenAIMockEngine()
        return FallbackNLPEngine()