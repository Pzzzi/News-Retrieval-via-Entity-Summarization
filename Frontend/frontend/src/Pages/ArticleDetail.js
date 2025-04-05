import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

function ArticleDetail() {
  const { id } = useParams();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [article, setArticle] = useState(null);

  useEffect(() => {
    const fetchArticleData = async () => {
      setLoading(true);
      try {
        const [summaryResponse, articleResponse] = await Promise.all([
          axios.get(`http://127.0.0.1:5000/article_summary/${id}`),
          axios.get(`http://127.0.0.1:5000/article/${id}`)
        ]);
        setSummary(summaryResponse.data.summary);
        setArticle(articleResponse.data);
      } catch (error) {
        console.error("Error fetching article data:", error);
        setSummary("No summary available.");
      }
      setLoading(false);
    };

    fetchArticleData();
  }, [id]);

  if (loading) return <p>Loading...</p>;

  return (
    <div className="article-detail">
      {article && (
        <>
          <h2>{article.title}</h2>
          <p className="article-meta">
            Published: {new Date(article.date).toLocaleDateString()}
          </p>
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            View original article
          </a>
        </>
      )}
      
      <div className="summary-section">
        <h3>Summary</h3>
        <div className="summary-content">
          {summary || "Loading summary..."}
        </div>
      </div>
    </div>
  );
}

export default ArticleDetail;