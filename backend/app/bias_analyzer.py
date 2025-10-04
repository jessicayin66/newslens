import re
from typing import Dict, List, Tuple
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import torch
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiasAnalyzer:
    def __init__(self):
        """Initialize the bias analyzer with various NLP models."""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {self.device}")
        
        # Initialize sentiment analyzer
        self.vader_analyzer = SentimentIntensityAnalyzer()
        
        # Political bias keywords (simplified approach)
        self.left_keywords = [
            'progressive', 'liberal', 'democrat', 'social justice', 'equality',
            'climate change', 'renewable energy', 'healthcare reform', 'minimum wage',
            'gun control', 'immigration reform', 'diversity', 'inclusion',
            'environmental protection', 'green energy', 'social welfare'
        ]
        
        self.right_keywords = [
            'conservative', 'republican', 'traditional values', 'free market',
            'small government', 'tax cuts', 'deregulation', 'law and order',
            'national security', 'border security', 'family values', 'religious freedom',
            'fiscal responsibility', 'entrepreneurship', 'individual liberty'
        ]
        
        # Don't load heavy models at startup to save memory
        self.bias_classifier = None
        self._model_loaded = False

    def analyze_bias(self, title: str, content: str) -> Dict[str, any]:
        """
        Analyze the political bias of an article.
        
        Args:
            title: Article title
            content: Article content/summary
            
        Returns:
            Dictionary containing bias analysis results
        """
        try:
            # Combine title and content for analysis
            full_text = f"{title}. {content}"
            
            # Clean text
            cleaned_text = self._clean_text(full_text)
            
            # Get keyword-based bias score
            keyword_bias = self._analyze_keyword_bias(cleaned_text)
            
            # Get sentiment-based analysis
            sentiment_analysis = self._analyze_sentiment(cleaned_text)
            
            # Get model-based analysis (if available)
            model_bias = self._analyze_with_model(cleaned_text)
            
            # Combine results
            bias_score = self._combine_bias_scores(keyword_bias, sentiment_analysis, model_bias)
            
            # Determine bias category
            bias_category = self._categorize_bias(bias_score)
            
            return {
                'bias_score': bias_score,
                'bias_category': bias_category,
                'confidence': self._calculate_confidence(keyword_bias, sentiment_analysis, model_bias),
                'details': {
                    'keyword_analysis': keyword_bias,
                    'sentiment_analysis': sentiment_analysis,
                    'model_analysis': model_bias
                }
            }
            
        except Exception as e:
            logger.error(f"Error in bias analysis: {e}")
            return {
                'bias_score': 0.0,
                'bias_category': 'neutral',
                'confidence': 0.0,
                'details': {'error': str(e)}
            }

    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text for analysis."""
        # Remove URLs, special characters, and extra whitespace
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip().lower()

    def _analyze_keyword_bias(self, text: str) -> Dict[str, float]:
        """Analyze bias based on political keywords."""
        left_count = sum(1 for keyword in self.left_keywords if keyword in text)
        right_count = sum(1 for keyword in self.right_keywords if keyword in text)
        
        total_keywords = left_count + right_count
        if total_keywords == 0:
            return {'left_score': 0.0, 'right_score': 0.0, 'neutral_score': 1.0}
        
        left_score = left_count / total_keywords
        right_score = right_count / total_keywords
        neutral_score = 1.0 - (left_score + right_score)
        
        return {
            'left_score': left_score,
            'right_score': right_score,
            'neutral_score': neutral_score
        }

    def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using VADER and TextBlob."""
        # VADER sentiment
        vader_scores = self.vader_analyzer.polarity_scores(text)
        
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        return {
            'vader_positive': vader_scores['pos'],
            'vader_negative': vader_scores['neg'],
            'vader_neutral': vader_scores['neu'],
            'vader_compound': vader_scores['compound'],
            'textblob_polarity': textblob_polarity,
            'textblob_subjectivity': textblob_subjectivity
        }

    def _load_bias_model(self):
        """Load the bias classification model only when needed."""
        if self._model_loaded:
            return
            
        try:
            logger.info("Loading bias classification model...")
            # Use a lighter model for memory efficiency
            self.bias_classifier = pipeline(
                "text-classification",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if self.device == "cuda" else -1
            )
            self._model_loaded = True
            logger.info("Loaded bias classification model")
        except Exception as e:
            logger.warning(f"Could not load bias model: {e}")
            self.bias_classifier = None
            self._model_loaded = True

    def _analyze_with_model(self, text: str) -> Dict[str, float]:
        """Analyze using transformer model if available."""
        # Load model only when needed
        self._load_bias_model()
        
        if not self.bias_classifier:
            return {'model_score': 0.0, 'model_confidence': 0.0}
        
        try:
            # Truncate text if too long
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            result = self.bias_classifier(text)
            
            # Convert sentiment to bias proxy
            if result[0]['label'] == 'LABEL_0':  # Negative
                model_score = -0.5
            elif result[0]['label'] == 'LABEL_1':  # Neutral
                model_score = 0.0
            else:  # Positive
                model_score = 0.5
            
            return {
                'model_score': model_score,
                'model_confidence': result[0]['score']
            }
        except Exception as e:
            logger.error(f"Error in model analysis: {e}")
            return {'model_score': 0.0, 'model_confidence': 0.0}

    def _combine_bias_scores(self, keyword_bias: Dict, sentiment: Dict, model_bias: Dict) -> float:
        """Combine different bias analysis methods into a single score."""
        # Weighted combination of different methods
        keyword_weight = 0.4
        sentiment_weight = 0.3
        model_weight = 0.3
        
        # Keyword-based score (-1 to 1, where -1 is left, 1 is right)
        keyword_score = keyword_bias['right_score'] - keyword_bias['left_score']
        
        # Sentiment-based score (compound sentiment as bias proxy)
        sentiment_score = sentiment['vader_compound'] * 0.5  # Scale down
        
        # Model-based score
        model_score = model_bias.get('model_score', 0.0)
        
        # Combine scores
        combined_score = (
            keyword_weight * keyword_score +
            sentiment_weight * sentiment_score +
            model_weight * model_score
        )
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, combined_score))

    def _categorize_bias(self, bias_score: float) -> str:
        """Categorize bias score into left/neutral/right."""
        if bias_score < -0.2:
            return 'left-leaning'
        elif bias_score > 0.2:
            return 'right-leaning'
        else:
            return 'neutral'

    def _calculate_confidence(self, keyword_bias: Dict, sentiment: Dict, model_bias: Dict) -> float:
        """Calculate confidence in the bias analysis."""
        # Simple confidence calculation based on agreement between methods
        keyword_strength = abs(keyword_bias['left_score'] - keyword_bias['right_score'])
        sentiment_strength = abs(sentiment['vader_compound'])
        model_confidence = model_bias.get('model_confidence', 0.5)
        
        # Average confidence
        confidence = (keyword_strength + sentiment_strength + model_confidence) / 3
        return min(1.0, confidence)

    def get_balanced_articles(self, articles: List[Dict], target_balance: Dict[str, int] = None) -> List[Dict]:
        """
        Filter articles to provide a balanced perspective.
        
        Args:
            articles: List of articles with bias information
            target_balance: Target distribution (e.g., {'left-leaning': 3, 'neutral': 4, 'right-leaning': 3})
        
        Returns:
            Balanced list of articles
        """
        if not target_balance:
            target_balance = {'left-leaning': 3, 'neutral': 4, 'right-leaning': 3}
        
        # Group articles by bias category
        bias_groups = {'left-leaning': [], 'neutral': [], 'right-leaning': []}
        
        for article in articles:
            bias_category = article.get('bias_category', 'neutral')
            if bias_category in bias_groups:
                bias_groups[bias_category].append(article)
        
        # Select articles to meet target balance
        balanced_articles = []
        for category, target_count in target_balance.items():
            available_articles = bias_groups.get(category, [])
            selected = available_articles[:target_count]
            balanced_articles.extend(selected)
        
        return balanced_articles
