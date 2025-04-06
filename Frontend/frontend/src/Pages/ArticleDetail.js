import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import '../styles/ArticleDetail.css';

function ArticleDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await axios.get(`http://127.0.0.1:5000/article_summary/${id}`);
        
        if (response.data.error) {
          throw new Error(response.data.error);
        }
        
        setSummaryData(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [id]);

  if (loading) return <div className="loading">Generating summary...</div>;
  if (error) return <div className="error">Error: {error}</div>;

  return (
    <div className="summary-container">
      <button onClick={() => navigate(-1)} className="back-button">
        &larr; Back to results
      </button>
      
      <h2>Summary: {summaryData?.article_title}</h2>
      
      <div className="summary-content">
        {summaryData?.summary || "No summary available"}
      </div>
      
      <a 
        href={summaryData?.article_url} 
        target="_blank" 
        rel="noopener noreferrer"
        className="original-link"
      >
        Read full article
      </a>
    </div>
  );
}

export default ArticleDetail;