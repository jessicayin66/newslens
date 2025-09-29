import { useEffect, useState } from "react";
import { fetchArticles } from "./services/api";
import TLDRSection from "./components/TLDRSection";
import "./App.css";

interface Article {
  title: string;
  source: string;
  summary: string;
  url: string;
  bias_analysis?: {
    bias_score: number;
    bias_category: string;
    confidence: number;
    details: any;
  };
}

export default function App() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const categories = ["All", "Business", "Entertainment", "Health", "Science", "Sports", "Technology"];

  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [selectedBias, setSelectedBias] = useState<string>("all");

  const loadArticles = async (category: string) => {
    setLoading(true);
    try {
      const fetchedArticles = await fetchArticles(category);
      setArticles(fetchedArticles);
    } catch (error) {
      console.error("Error fetching articles:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadArticles(selectedCategory);
  }, [selectedCategory]);

  // Group articles by topic/cluster for bias distribution analysis
  const groupArticlesByTopic = (articles: Article[]) => {
    const topicGroups: { [key: string]: Article[] } = {};
    
    articles.forEach(article => {
      // Simple topic extraction based on keywords in title
      const title = article.title.toLowerCase();
      let topic = "All";
      
      if (title.includes("climate") || title.includes("environment") || title.includes("green")) {
        topic = "Climate & Environment";
      } else if (title.includes("economy") || title.includes("market") || title.includes("business") || title.includes("financial")) {
        topic = "Economy & Business";
      } else if (title.includes("health") || title.includes("medical") || title.includes("covid") || title.includes("pandemic")) {
        topic = "Health & Medicine";
      } else if (title.includes("technology") || title.includes("ai") || title.includes("tech") || title.includes("digital")) {
        topic = "Technology";
      } else if (title.includes("politics") || title.includes("election") || title.includes("government") || title.includes("policy")) {
        topic = "Politics & Government";
      } else if (title.includes("international") || title.includes("foreign") || title.includes("war") || title.includes("conflict")) {
        topic = "International Affairs";
      }
      
      if (!topicGroups[topic]) {
        topicGroups[topic] = [];
      }
      topicGroups[topic].push(article);
    });
    
    return topicGroups;
  };

  // Calculate bias distribution for a group of articles
  const calculateBiasDistribution = (articles: Article[]) => {
    const total = articles.length;
    if (total === 0) return { left: 0, neutral: 0, right: 0 };
    
    const distribution = { left: 0, neutral: 0, right: 0 };
    
    articles.forEach(article => {
      const biasCategory = article.bias_analysis?.bias_category || "neutral";
      if (biasCategory === "left-leaning") distribution.left++;
      else if (biasCategory === "right-leaning") distribution.right++;
      else distribution.neutral++;
    });
    
    return {
      left: Math.round((distribution.left / total) * 100),
      neutral: Math.round((distribution.neutral / total) * 100),
      right: Math.round((distribution.right / total) * 100)
    };
  };

  const allTopicGroups = groupArticlesByTopic(articles);
  
  // Get the topic group for the selected category
  const getTopicForCategory = (category: string) => {
    if (category === "All") {
      return "All";
    } else if (category === "Business") {
      return "Economy & Business";
    } else if (category === "Health") {
      return "Health & Medicine";
    } else if (category === "Technology") {
      return "Technology";
    } else if (category === "Entertainment") {
      return "Entertainment";
    } else if (category === "Science") {
      return "Science";
    } else if (category === "Sports") {
      return "Sports";
    }
    return category; // Return the category name as the topic
  };
  
  const selectedTopic = getTopicForCategory(selectedCategory);
  const topicArticles = allTopicGroups[selectedTopic] || [];
  
  // Filter articles by bias if a specific bias is selected
  const currentTopicArticles = topicArticles.filter(article => {
    if (selectedBias === "all") return true;
    if (!article.bias_analysis) return selectedBias === "neutral";
    return article.bias_analysis.bias_category === selectedBias;
  });

  // Handle bias filtering
  const handleBiasFilter = (bias: string) => {
    setSelectedBias(bias);
  };

  return (
    <div className="app-container">
      <div className="logo-container">
        <h1>NewsLens</h1>
      </div>
      
      {/* Category Toolbar */}
      <div className="category-toolbar">
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            disabled={loading}
            className={`category-button ${
              selectedCategory === cat ? "active" : "inactive"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Bias Distribution View */}
      <div className="bias-distribution-container">
        {loading ? (
          <div className="loading-container">
            <div className="loading-text">
              <div className="loading-spinner"></div>
              Loading articles...
            </div>
          </div>
        ) : (
          <div className="topic-cluster">
            <div className="cluster-header">
              <h3 className="cluster-title">{selectedTopic}</h3>
              <div className="bias-distribution-meter">
                <div className="distribution-bar">
                  <div 
                    className={`distribution-segment left ${selectedBias === "left-leaning" ? "active" : ""}`}
                    style={{ width: `${calculateBiasDistribution(topicArticles).left}%` }}
                    title={`${calculateBiasDistribution(topicArticles).left}% Left-leaning - Click to filter`}
                    onClick={() => handleBiasFilter(selectedBias === "left-leaning" ? "all" : "left-leaning")}
                  ></div>
                  <div 
                    className={`distribution-segment neutral ${selectedBias === "neutral" ? "active" : ""}`}
                    style={{ width: `${calculateBiasDistribution(topicArticles).neutral}%` }}
                    title={`${calculateBiasDistribution(topicArticles).neutral}% Neutral - Click to filter`}
                    onClick={() => handleBiasFilter(selectedBias === "neutral" ? "all" : "neutral")}
                  ></div>
                  <div 
                    className={`distribution-segment right ${selectedBias === "right-leaning" ? "active" : ""}`}
                    style={{ width: `${calculateBiasDistribution(topicArticles).right}%` }}
                    title={`${calculateBiasDistribution(topicArticles).right}% Right-leaning - Click to filter`}
                    onClick={() => handleBiasFilter(selectedBias === "right-leaning" ? "all" : "right-leaning")}
                  ></div>
                </div>
                <div className="distribution-labels">
                  <span 
                    className={`distribution-label left ${selectedBias === "left-leaning" ? "active" : ""}`}
                    onClick={() => handleBiasFilter(selectedBias === "left-leaning" ? "all" : "left-leaning")}
                  >
                    {calculateBiasDistribution(topicArticles).left}% Left
                  </span>
                  <span 
                    className={`distribution-label neutral ${selectedBias === "neutral" ? "active" : ""}`}
                    onClick={() => handleBiasFilter(selectedBias === "neutral" ? "all" : "neutral")}
                  >
                    {calculateBiasDistribution(topicArticles).neutral}% Neutral
                  </span>
                  <span 
                    className={`distribution-label right ${selectedBias === "right-leaning" ? "active" : ""}`}
                    onClick={() => handleBiasFilter(selectedBias === "right-leaning" ? "all" : "right-leaning")}
                  >
                    {calculateBiasDistribution(topicArticles).right}% Right
                  </span>
                </div>
              </div>
            </div>
            
            {/* TL;DR Section */}
            <TLDRSection category={selectedCategory} />
            
            <div className="articles-grid">
              {currentTopicArticles.map((article, i) => (
                <div key={i} className="article-card">
                  <div className="article-header">
                    <h4 className="article-title">{article.title}</h4>
                    {article.bias_analysis && (
                      <div className={`bias-tag ${article.bias_analysis.bias_category}`}>
                        <span className="bias-tag-label">{article.bias_analysis.bias_category}</span>
                        <div className="bias-confidence">
                          {Math.round(article.bias_analysis.confidence * 100)}%
                        </div>
                      </div>
                    )}
                  </div>
                  <p className="article-source">{article.source}</p>
                  <p className="article-summary">{article.summary}</p>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="article-link"
                  >
                    Read full article →
                  </a>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );  
}