import { useEffect, useState } from "react";
import { fetchArticles } from "./services/api";

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
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">AI News Summarizer</h1>
      <div className="space-y-4">
        {articles.map((a, i) => (
          <div
            key={i}
            className="border-l-4 border-blue-500 bg-white rounded-lg shadow-md p-4 hover:bg-gray-50 transition-colors"
          >
            <h2 className="text-lg font-bold mb-1">{a.title}</h2>
            <p className="text-gray-500 text-sm mb-2">{a.source}</p>
            <p className="text-gray-700">{a.summary}</p>
            <a
              href={a.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 mt-2 inline-block hover:underline"
            >
              Read full article →
            </a>
          </div>
        ))}
      </div>
    </div>
  );  
}