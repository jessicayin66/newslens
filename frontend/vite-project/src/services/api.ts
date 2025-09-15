export async function fetchArticles() {
    const res = await fetch("/articles");
    if (!res.ok) {
      throw new Error("Failed to fetch articles");
    }
    return res.json();
  }
  