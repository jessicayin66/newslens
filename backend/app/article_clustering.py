import logging
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans, DBSCAN
from collections import Counter
import re

logger = logging.getLogger(__name__)

class ArticleClusterer:
    def __init__(self):
        """Initialize the article clustering service."""
        self.embedding_model = None
        self._model_loaded = False
        # Don't load models at startup to save memory
    
    def _load_models(self):
        """Load the sentence embedding model only when needed."""
        if self._model_loaded:
            return
            
        try:
            logger.info("Loading sentence embedding model...")
            # Use a smaller, more memory-efficient model
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2', use_auth_token=False)
            self._model_loaded = True
            logger.info("Sentence embedding model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            # Fallback to a simpler approach - we'll use basic text similarity
            self.embedding_model = None
            self._model_loaded = True
            logger.info("Using fallback text similarity approach")
    
    def extract_entities(self, text: str) -> List[str]:
        """Extract key entities from text using simple regex patterns."""
        entities = []
        
        # Extract capitalized words (potential proper nouns)
        capitalized_words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        entities.extend(capitalized_words)
        
        # Extract common organization patterns
        org_patterns = [
            r'\b[A-Z][a-z]+\s+(Inc|Corp|LLC|Ltd|Company|Corporation)\b',
            r'\b[A-Z][a-z]+\s+(University|College|Institute)\b',
            r'\b[A-Z][a-z]+\s+(Bank|Financial|Group)\b'
        ]
        
        for pattern in org_patterns:
            matches = re.findall(pattern, text)
            entities.extend(matches)
        
        return entities
    
    def cluster_articles(self, articles: List[Dict[str, Any]], 
                        min_cluster_size: int = 3, 
                        max_clusters: int = 10) -> List[Dict[str, Any]]:
        """
        Cluster articles by topic similarity.
        
        Args:
            articles: List of article dictionaries
            min_cluster_size: Minimum number of articles per cluster
            max_clusters: Maximum number of clusters to create
            
        Returns:
            List of clusters with their articles and summaries
        """
        if len(articles) < min_cluster_size:
            # If too few articles, return as single cluster
            return [{
                "cluster_id": 0,
                "articles": articles,
                "summary": self._create_cluster_summary(articles),
                "key_entities": self._extract_cluster_entities(articles),
                "size": len(articles)
            }]
        
        try:
            # Prepare text for embedding
            texts = []
            for article in articles:
                # Combine title and description for better clustering
                text = f"{article.get('title', '')} {article.get('content', '')}"
                texts.append(text)
            
            # Try to load model if not already loaded
            self._load_models()
            
            # Generate embeddings or use fallback
            if self.embedding_model is not None:
                logger.info(f"Generating embeddings for {len(texts)} articles...")
                embeddings = self.embedding_model.encode(texts)
            else:
                logger.info("Using fallback keyword-based clustering...")
                return self._fallback_clustering(articles, min_cluster_size, max_clusters)
            
            # Determine optimal number of clusters
            n_clusters = min(max_clusters, max(2, len(articles) // min_cluster_size))
            
            # Perform clustering using DBSCAN for better cluster shapes
            clusterer = DBSCAN(
                eps=0.3,  # Distance threshold
                min_samples=min_cluster_size,
                metric='cosine'
            )
            
            cluster_labels = clusterer.fit_predict(embeddings)
            
            # Handle noise points (label -1) by assigning to nearest cluster
            if -1 in cluster_labels:
                noise_indices = np.where(cluster_labels == -1)[0]
                for idx in noise_indices:
                    # Find nearest cluster
                    distances = []
                    for cluster_id in set(cluster_labels):
                        if cluster_id != -1:
                            cluster_embeddings = embeddings[cluster_labels == cluster_id]
                            if len(cluster_embeddings) > 0:
                                mean_embedding = np.mean(cluster_embeddings, axis=0)
                                distance = np.linalg.norm(embeddings[idx] - mean_embedding)
                                distances.append((distance, cluster_id))
                    
                    if distances:
                        _, nearest_cluster = min(distances)
                        cluster_labels[idx] = nearest_cluster
            
            # Group articles by cluster
            clusters = {}
            for i, label in enumerate(cluster_labels):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(articles[i])
            
            # Create cluster summaries
            cluster_results = []
            for cluster_id, cluster_articles in clusters.items():
                if len(cluster_articles) >= min_cluster_size:
                    cluster_summary = {
                        "cluster_id": cluster_id,
                        "articles": cluster_articles,
                        "summary": self._create_cluster_summary(cluster_articles),
                        "key_entities": self._extract_cluster_entities(cluster_articles),
                        "size": len(cluster_articles)
                    }
                    cluster_results.append(cluster_summary)
            
            # Sort by cluster size (largest first)
            cluster_results.sort(key=lambda x: x["size"], reverse=True)
            
            logger.info(f"Created {len(cluster_results)} clusters from {len(articles)} articles")
            return cluster_results
            
        except Exception as e:
            logger.error(f"Error clustering articles: {e}")
            # Fallback: return all articles as single cluster
            return [{
                "cluster_id": 0,
                "articles": articles,
                "summary": self._create_cluster_summary(articles),
                "key_entities": self._extract_cluster_entities(articles),
                "size": len(articles)
            }]
    
    def _extract_cluster_entities(self, articles: List[Dict[str, Any]]) -> List[str]:
        """Extract key entities from a cluster of articles."""
        all_entities = []
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('content', '')}"
            entities = self.extract_entities(text)
            all_entities.extend(entities)
        
        # Count entity frequency and return most common
        entity_counts = Counter(all_entities)
        # Filter out very short entities and return top entities
        top_entities = [
            entity for entity, count in entity_counts.most_common(10)
            if len(entity) > 2 and count > 1
        ]
        
        return top_entities[:5]  # Return top 5 entities
    
    def _create_cluster_summary(self, articles: List[Dict[str, Any]]) -> str:
        """Create a summary for a cluster of articles."""
        if not articles:
            return "No articles in cluster"
        
        if len(articles) == 1:
            return articles[0].get('title', 'No title available')
        
        # Extract titles and descriptions
        titles = [article.get('title', '') for article in articles if article.get('title')]
        descriptions = [article.get('content', '') for article in articles if article.get('content')]
        
        # Find common themes in titles
        common_words = self._find_common_theme(titles)
        
        # Create a simple summary based on most representative title
        if titles:
            # Use the longest title as it's likely most descriptive
            main_title = max(titles, key=len)
            
            if common_words:
                return f"{main_title} (Related to: {', '.join(common_words[:3])})"
            else:
                return main_title
        
        return "Multiple related articles"
    
    def _find_common_theme(self, titles: List[str]) -> List[str]:
        """Find common words/themes across titles."""
        if len(titles) < 2:
            return []
        
        # Extract words from titles
        all_words = []
        for title in titles:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
            all_words.extend(words)
        
        # Count word frequency
        word_counts = Counter(all_words)
        
        # Filter out common stop words
        stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'man', 'oil', 'sit', 'try', 'use', 'way', 'with', 'this', 'that', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'}
        
        # Get common words (appearing in multiple titles)
        common_words = [
            word for word, count in word_counts.most_common(10)
            if word not in stop_words and count > 1
        ]
        
        return common_words
    
    def _fallback_clustering(self, articles: List[Dict[str, Any]], 
                           min_cluster_size: int, max_clusters: int) -> List[Dict[str, Any]]:
        """Fallback clustering using keyword similarity when embeddings fail."""
        try:
            # Group articles by common keywords
            keyword_groups = {}
            
            for article in articles:
                title = article.get('title', '').lower()
                content = article.get('content', '').lower()
                text = f"{title} {content}"
                
                # Extract key terms
                words = re.findall(r'\b[a-zA-Z]{4,}\b', text)
                word_counts = Counter(words)
                
                # Get top keywords
                top_keywords = [word for word, count in word_counts.most_common(5) 
                              if word not in {'this', 'that', 'with', 'from', 'they', 'have', 'been', 'will', 'said', 'more', 'than', 'also', 'each', 'which', 'their', 'time', 'very', 'when', 'much', 'new', 'some', 'these', 'may', 'other', 'after', 'first', 'well', 'year', 'work', 'such', 'make', 'over', 'think', 'also', 'back', 'where', 'much', 'before', 'move', 'right', 'boy', 'old', 'too', 'same', 'she', 'all', 'there', 'when', 'up', 'use', 'word', 'how', 'said', 'an', 'each', 'which', 'do', 'their', 'time', 'if', 'will', 'about', 'out', 'many', 'then', 'them', 'can', 'only', 'other', 'new', 'some', 'what', 'time', 'very', 'when', 'much', 'get', 'through', 'back', 'much', 'before', 'go', 'good', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us'}]
                
                # Find or create group based on top keywords
                assigned = False
                for keyword in top_keywords[:3]:  # Use top 3 keywords
                    if keyword in keyword_groups:
                        keyword_groups[keyword].append(article)
                        assigned = True
                        break
                
                if not assigned and top_keywords:
                    # Create new group with first keyword
                    keyword_groups[top_keywords[0]] = [article]
            
            # Convert to cluster format
            clusters = []
            for i, (keyword, group_articles) in enumerate(keyword_groups.items()):
                if len(group_articles) >= min_cluster_size:
                    clusters.append({
                        "cluster_id": i,
                        "articles": group_articles,
                        "summary": self._create_cluster_summary(group_articles),
                        "key_entities": self._extract_cluster_entities(group_articles),
                        "size": len(group_articles)
                    })
            
            # Sort by size and limit
            clusters.sort(key=lambda x: x["size"], reverse=True)
            return clusters[:max_clusters]
            
        except Exception as e:
            logger.error(f"Error in fallback clustering: {e}")
            # Return single cluster with all articles
            return [{
                "cluster_id": 0,
                "articles": articles,
                "summary": self._create_cluster_summary(articles),
                "key_entities": self._extract_cluster_entities(articles),
                "size": len(articles)
            }]

# Global instance
article_clusterer = ArticleClusterer()
