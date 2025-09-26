import { useEffect, useState } from "react";
import { fetchArticles } from "./services/api";
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
  const [biasFilter, setBiasFilter] = useState<string>("all");
  const [showBalancedDiet, setShowBalancedDiet] = useState<boolean>(false);

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

  // Filter articles based on bias
  const filteredArticles = articles.filter(article => {
    if (biasFilter === "all") return true;
    if (!article.bias_analysis) return biasFilter === "neutral";
    return article.bias_analysis.bias_category === biasFilter;
  });

  return (
    <div className="app-container">
      <h1>NewsQuest</h1>
      
      {/* Bias Filter Section */}
      <div className="bias-filter-section">
        <div className="bias-filter-header">
          <h2>Bias Analysis</h2>
          <button 
            className="balanced-diet-button"
            onClick={() => setShowBalancedDiet(!showBalancedDiet)}
          >
            {showBalancedDiet ? "Show All" : "Balanced Diet"}
          </button>
        </div>
        
        <div className="bias-filters">
          <button
            className={`bias-filter-btn ${biasFilter === "all" ? "active" : ""}`}
            onClick={() => setBiasFilter("all")}
          >
            All Articles
          </button>
          <button
            className={`bias-filter-btn ${biasFilter === "left-leaning" ? "active" : ""}`}
            onClick={() => setBiasFilter("left-leaning")}
          >
            Left-Leaning
          </button>
          <button
            className={`bias-filter-btn ${biasFilter === "neutral" ? "active" : ""}`}
            onClick={() => setBiasFilter("neutral")}
          >
            Neutral
          </button>
          <button
            className={`bias-filter-btn ${biasFilter === "right-leaning" ? "active" : ""}`}
            onClick={() => setBiasFilter("right-leaning")}
          >
            Right-Leaning
          </button>
        </div>
      </div>

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
      <div className="articles-grid">
        {loading ? (
          <div className="loading-container">
            <div className="loading-text">
              <div className="loading-spinner"></div>
              Loading articles...
            </div>
          </div>
        ) : (
          filteredArticles.map((a, i) => (
            <div key={i} className="article-card">
              <div className="article-header">
                <h2 className="article-title">{a.title}</h2>
                {a.bias_analysis && (
                  <div className={`bias-indicator ${a.bias_analysis.bias_category}`}>
                    <span className="bias-label">{a.bias_analysis.bias_category}</span>
                    <div className="bias-confidence">
                      {Math.round(a.bias_analysis.confidence * 100)}%
                    </div>
                  </div>
                )}
              </div>
              <p className="article-source">{a.source}</p>
              <p className="article-summary">{a.summary}</p>
              <a
                href={a.url}
                target="_blank"
                rel="noopener noreferrer"
                className="article-link"
              >
                Read full article →
              </a>
            </div>
          ))
        )}
      </div>
    </div>
  );  
}