import { useEffect, useState } from "react";
import { fetchArticles } from "./services/api";
import "./App.css";

interface Article {
  title: string;
  source: string;
  summary: string;
  url: string;
}

export default function App() {
  const [articles, setArticles] = useState<Article[]>([]);

  useEffect(() => {
    fetchArticles()
      .then(setArticles)
      .catch(console.error);
  }, []);

  return (
    <div className="app-container">
      <h1>AI News Summarizer</h1>
      <div className="articles-grid">
        {articles.map((a, i) => (
          <div key={i} className="article-card">
            <h2 className="article-title">{a.title}</h2>
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
        ))}
      </div>
    </div>
  );  
}