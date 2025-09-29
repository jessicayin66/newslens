import logging
from typing import List, Dict, Any
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.text_rank import TextRankSummarizer
from sumy.summarizers.lsa import LsaSummarizer
from transformers import pipeline
import re

logger = logging.getLogger(__name__)

class SummarizationService:
    def __init__(self):
        """Initialize the summarization service."""
        self.textrank_summarizer = TextRankSummarizer()
        self.lsa_summarizer = LsaSummarizer()
        self.transformer_summarizer = None
        self._load_models()
    
    def _load_models(self):
        """Load summarization models."""
        try:
            logger.info("Loading transformer summarization model...")
            # Use a smaller, faster model for summarization
            try:
                self.transformer_summarizer = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    device=-1,  # Use CPU
                    max_length=100,
                    min_length=30
                )
                logger.info("Transformer summarization model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
                self.transformer_summarizer = None
                logger.info("Falling back to extractive summarization only")
        except Exception as e:
            logger.error(f"Error loading transformer model: {e}")
            logger.info("Falling back to extractive summarization only")
            self.transformer_summarizer = None
    
    def create_tldr_summary(self, cluster: Dict[str, Any], 
                           method: str = "hybrid") -> str:
        """
        Create a TL;DR summary for a cluster of articles.
        
        Args:
            cluster: Cluster dictionary with articles and metadata
            method: Summarization method ("extractive", "abstractive", "hybrid")
            
        Returns:
            TL;DR summary string
        """
        articles = cluster.get("articles", [])
        if not articles:
            return "No articles to summarize"
        
        if len(articles) == 1:
            return self._summarize_single_article(articles[0])
        
        # Combine text from all articles in cluster
        combined_text = self._combine_cluster_text(articles)
        
        if method == "extractive":
            return self._extractive_summary(combined_text)
        elif method == "abstractive" and self.transformer_summarizer:
            return self._abstractive_summary(combined_text)
        else:  # hybrid or fallback
            return self._hybrid_summary(combined_text, cluster)
    
    def _summarize_single_article(self, article: Dict[str, Any]) -> str:
        """Create summary for a single article."""
        title = article.get("title", "")
        content = article.get("content", "")
        
        if not content:
            return title
        
        # If content is short, return title
        if len(content.split()) < 20:
            return title
        
        # Create a brief summary
        try:
            if self.transformer_summarizer:
                summary = self.transformer_summarizer(
                    content,
                    max_length=50,
                    min_length=10,
                    do_sample=False
                )
                return self._clean_summary_text(summary[0]["summary_text"])
            else:
                return self._clean_summary_text(self._extractive_summary(content, max_sentences=1))
        except Exception as e:
            logger.error(f"Error summarizing single article: {e}")
            return title
    
    def _combine_cluster_text(self, articles: List[Dict[str, Any]]) -> str:
        """Combine text from all articles in a cluster."""
        combined_parts = []
        
        for article in articles:
            title = article.get("title", "")
            content = article.get("content", "")
            
            if title:
                combined_parts.append(title)
            
            if content and len(content.split()) > 10:  # Only add substantial content
                # Truncate very long content
                words = content.split()
                if len(words) > 100:
                    content = " ".join(words[:100]) + "..."
                combined_parts.append(content)
        
        return " ".join(combined_parts)
    
    def _extractive_summary(self, text: str, max_sentences: int = 2) -> str:
        """Create extractive summary using TextRank or LSA."""
        try:
            # Clean and prepare text
            text = self._clean_text(text)
            
            if len(text.split()) < 50:
                return text
            
            # Parse text
            parser = PlaintextParser.from_string(text, Tokenizer("english"))
            
            # Try TextRank first
            try:
                summary_sentences = self.textrank_summarizer(parser.document, max_sentences)
                if summary_sentences:
                    summary = " ".join([str(sentence) for sentence in summary_sentences])
                    return self._clean_summary_text(summary)
            except Exception as e:
                logger.warning(f"TextRank failed: {e}")
            
            # Fallback to LSA
            try:
                summary_sentences = self.lsa_summarizer(parser.document, max_sentences)
                if summary_sentences:
                    summary = " ".join([str(sentence) for sentence in summary_sentences])
                    return self._clean_summary_text(summary)
            except Exception as e:
                logger.warning(f"LSA failed: {e}")
            
            # Final fallback: return first few sentences
            sentences = text.split('. ')
            summary = '. '.join(sentences[:max_sentences]) + '.'
            return self._clean_summary_text(summary)
            
        except Exception as e:
            logger.error(f"Error in extractive summarization: {e}")
            # Return truncated text as fallback
            words = text.split()
            fallback = " ".join(words[:30]) + "..." if len(words) > 30 else text
            return self._clean_summary_text(fallback)
    
    def _abstractive_summary(self, text: str) -> str:
        """Create abstractive summary using transformer model."""
        try:
            if not self.transformer_summarizer:
                return self._extractive_summary(text)
            
            # Clean text
            text = self._clean_text(text)
            
            # Truncate if too long
            words = text.split()
            if len(words) > 500:
                text = " ".join(words[:500])
            
            # Generate summary
            summary = self.transformer_summarizer(
                text,
                max_length=80,
                min_length=20,
                do_sample=False
            )
            
            return self._clean_summary_text(summary[0]["summary_text"])
            
        except Exception as e:
            logger.error(f"Error in abstractive summarization: {e}")
            return self._extractive_summary(text)
    
    def _hybrid_summary(self, text: str, cluster: Dict[str, Any]) -> str:
        """Create hybrid summary combining multiple methods."""
        try:
            # Get key entities from cluster
            key_entities = cluster.get("key_entities", [])
            
            # Try abstractive first if available
            if self.transformer_summarizer:
                abstractive_summary = self._abstractive_summary(text)
                
                # Enhance with key entities if they're not mentioned
                # Clean up the summary
                abstractive_summary = self._clean_summary_text(abstractive_summary)
                
                return abstractive_summary
            else:
                # Use extractive with entity enhancement
                extractive_summary = self._extractive_summary(text)
                
                # Clean up the summary
                extractive_summary = self._clean_summary_text(extractive_summary)
                
                return extractive_summary
                
        except Exception as e:
            logger.error(f"Error in hybrid summarization: {e}")
            return self._extractive_summary(text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for summarization."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep sentence structure
        text = re.sub(r'[^\w\s\.\,\!\?\-]', '', text)
        
        return text.strip()
    
    def _clean_summary_text(self, text: str) -> str:
        """Clean summary text to remove formatting artifacts and ranking numbers."""
        # Remove ranking numbers like "No. 6", "No.3", etc. (with or without space)
        text = re.sub(r'No\.\s*\d+\s*', '', text)
        
        # Remove standalone "The:" at the beginning
        text = re.sub(r'^The:\s*', '', text)
        
        # Remove other common prefixes that might be artifacts
        text = re.sub(r'^(The|A|An):\s*', '', text)
        
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure proper sentence structure
        text = text.strip()
        
        # If the text starts with a lowercase letter, capitalize it
        if text and text[0].islower():
            text = text[0].upper() + text[1:]
        
        return text

    def create_category_tldr(self, clusters: List[Dict[str, Any]], 
                           category: str, max_summaries: int = 5) -> Dict[str, Any]:
        """
        Create TL;DR summaries for all clusters in a category.
        
        Args:
            clusters: List of cluster dictionaries
            category: News category name
            max_summaries: Maximum number of summaries to include
            
        Returns:
            Dictionary with category TL;DR information
        """
        try:
            # Sort clusters by size (most articles first)
            sorted_clusters = sorted(clusters, key=lambda x: x.get("size", 0), reverse=True)
            
            # Create summaries for top clusters
            summaries = []
            for i, cluster in enumerate(sorted_clusters[:max_summaries]):
                try:
                    summary_text = self.create_tldr_summary(cluster, method="hybrid")
                    summaries.append({
                        "rank": i + 1,
                        "summary": summary_text,
                        "article_count": cluster.get("size", 0),
                        "key_entities": cluster.get("key_entities", [])[:3]
                    })
                except Exception as e:
                    logger.error(f"Error creating summary for cluster {i}: {e}")
                    continue
            
            return {
                "category": category,
                "date": "Today",  # Could be made dynamic
                "total_clusters": len(clusters),
                "total_articles": sum(cluster.get("size", 0) for cluster in clusters),
                "summaries": summaries
            }
            
        except Exception as e:
            logger.error(f"Error creating category TL;DR: {e}")
            return {
                "category": category,
                "date": "Today",
                "total_clusters": 0,
                "total_articles": 0,
                "summaries": []
            }

# Global instance
summarization_service = SummarizationService()
