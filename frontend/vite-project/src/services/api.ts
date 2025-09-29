export async function fetchArticles(category: string = "all") {
    const url = category === "All" ? "/articles" : `/articles?category=${category.toLowerCase()}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error("Failed to fetch articles");
    }
    return res.json();
  }

// TL;DR API functions
export interface TLDRSummary {
  rank: number;
  summary: string;
  article_count: number;
  key_entities: string[];
}

export interface TLDRResponse {
  category: string;
  date: string;
  total_clusters: number;
  total_articles: number;
  summaries: TLDRSummary[];
  generated_at?: string;
  error?: string;
}

export async function fetchTLDR(category: string = "all", forceRefresh: boolean = false): Promise<TLDRResponse> {
  const url = category === "All" ? "/tldr/all" : `/tldr/${category.toLowerCase()}`;
  const params = forceRefresh ? "?force_refresh=true" : "";
  const res = await fetch(url + params);
  if (!res.ok) {
    throw new Error("Failed to fetch TL;DR summaries");
  }
  return res.json();
}

export interface TrendingTopic {
  topic: string;
  article_count: number;
  key_entities: string[];
  rank: number;
}

export interface TrendingResponse {
  category: string;
  trending_topics: TrendingTopic[];
  count: number;
  error?: string;
}

export async function fetchTrendingTopics(category: string = "all"): Promise<TrendingResponse> {
  const url = category === "All" ? "/trending/all" : `/trending/${category.toLowerCase()}`;
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error("Failed to fetch trending topics");
  }
  return res.json();
}
  