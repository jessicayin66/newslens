type ArticleProps = {
    title: string;
    summary: string;
    url: string;
    source: string;
  };
  
  export default function ArticleCard({ title, summary, url, source }: ArticleProps) {
    return (
      <div className="p-4 border rounded-lg shadow-md mb-3">
        <h2 className="text-lg font-bold">{title}</h2>
        <p className="text-sm italic">{source}</p>
        <p className="mt-2">{summary}</p>
        <a href={url} target="_blank" rel="noopener noreferrer" className="text-blue-500 mt-2 block">
          Read full article →
        </a>
      </div>
    );
  }
  