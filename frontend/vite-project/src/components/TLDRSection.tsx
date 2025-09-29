import React, { useState, useEffect } from 'react';
import { fetchTLDR } from '../services/api';

// Define types locally to avoid import issues
interface TLDRSummary {
  rank: number;
  summary: string;
  article_count: number;
  key_entities: string[];
}

interface TLDRResponse {
  category: string;
  date: string;
  total_clusters: number;
  total_articles: number;
  summaries: TLDRSummary[];
  generated_at?: string;
  error?: string;
}

interface TLDRSectionProps {
  category: string;
  onRefresh?: () => void;
}

export default function TLDRSection({ category, onRefresh }: TLDRSectionProps) {
  const [tldrData, setTldrData] = useState<TLDRResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showDetails, setShowDetails] = useState<boolean>(false);

  const loadTLDR = async (forceRefresh: boolean = false) => {
    setLoading(true);
    setError(null);
    try {
      console.log(`Loading TL;DR for category: ${category}`);
      const data = await fetchTLDR(category, forceRefresh);
      console.log('TL;DR data received:', data);
      setTldrData(data);
    } catch (err) {
      console.error('TL;DR loading error:', err);
      setError(err instanceof Error ? err.message : 'Failed to load TL;DR summaries');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTLDR();
  }, [category]);

  const handleRefresh = () => {
    loadTLDR(true);
    onRefresh?.();
  };

  if (loading && !tldrData) {
    return (
      <div className="tldr-section">
        <div className="tldr-header">
          <h3>📰 TL;DR Summary</h3>
        </div>
        <div className="tldr-loading">
          <div className="loading-spinner"></div>
          <span>Generating summaries...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tldr-section">
        <div className="tldr-header">
          <h3>📰 TL;DR Summary</h3>
          <button onClick={handleRefresh} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
        <div className="tldr-error">
          <p>❌ {error}</p>
          <button onClick={handleRefresh} className="retry-button">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!tldrData || tldrData.summaries.length === 0) {
    return (
      <div className="tldr-section">
        <div className="tldr-header">
          <h3>📰 TL;DR Summary</h3>
          <button onClick={handleRefresh} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
        <div className="tldr-empty">
          <p>No summaries available for this category.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="tldr-section">
      <div className="tldr-header">
        <h3>📰 TL;DR Summary</h3>
        <div className="tldr-controls">
          <button 
            onClick={() => setShowDetails(!showDetails)} 
            className="toggle-details-button"
          >
            {showDetails ? '📋 Hide Details' : '📊 Show Details'}
          </button>
          <button onClick={handleRefresh} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
      </div>

      {showDetails && (
        <div className="tldr-stats">
          <div className="stat-item">
            <span className="stat-label">Articles Analyzed:</span>
            <span className="stat-value">{tldrData.total_articles}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Story Clusters:</span>
            <span className="stat-value">{tldrData.total_clusters}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Generated:</span>
            <span className="stat-value">
              {new Date(tldrData.generated_at || tldrData.date).toLocaleTimeString()}
            </span>
          </div>
        </div>
      )}

      <div className="tldr-summaries">
        {tldrData.summaries.map((summary: TLDRSummary) => (
          <div key={summary.rank} className="tldr-summary-card">
            <div className="summary-header">
              <div className="summary-rank">#{summary.rank}</div>
              <div className="summary-meta">
                <span className="article-count">{summary.article_count} articles</span>
              </div>
            </div>
                    <div className="summary-content">
                      <ul>
                        {summary.summary.split('. ').filter(sentence => sentence.trim()).map((sentence, idx) => (
                          <li key={idx}>{sentence.trim()}{sentence.endsWith('.') ? '' : '.'}</li>
                        ))}
                      </ul>
                    </div>
          </div>
        ))}
      </div>

      {loading && (
        <div className="tldr-loading-overlay">
          <div className="loading-spinner"></div>
          <span>Updating summaries...</span>
        </div>
      )}
    </div>
  );
}
