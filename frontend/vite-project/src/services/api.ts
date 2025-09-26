export async function fetchArticles(category: string = "all") {
    const url = category === "All" ? "/articles" : `/articles?category=${category.toLowerCase()}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error("Failed to fetch articles");
    }
    return res.json();
  }
  