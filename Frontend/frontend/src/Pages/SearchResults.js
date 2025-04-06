import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import EntityGraph from '../Components/EntityGraph';
import ArticleCard from '../Components/ArticleCard'; 
import '../styles/ArticleResults.css'; 

function SearchResults() {
  const { entity } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(
          `http://127.0.0.1:5000/search?entity=${entity}`,
          { timeout: 10000 } // 10 second timeout
        );
        
        // Validate response structure
        if (!response.data?.entity || !response.data?.articles) {
          throw new Error('Invalid API response structure');
        }
        
        setData(response.data);
      } catch (error) {
        console.error("Error fetching data:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [entity]);

  const handleEntityClick = (newEntity) => {
    navigate(`/search/${newEntity}`);
  };

  const handleArticleClick = (articleId) => {
    navigate(`/article/${articleId}`);
  };

  if (loading) {
    return (
      <div className="loading-state">
        <p>Loading results for "{entity}"...</p>
        {/* You could add a spinner here */}
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-state">
        <p>Error loading results: {error}</p>
        <button onClick={() => window.location.reload()}>Try Again</button>
      </div>
    );
  }

  if (!data || !data.articles?.length) {
    return (
      <div className="empty-state">
        <p>No articles found for "{entity}"</p>
        <p>Try searching for something else</p>
      </div>
    );
  }

  return (
    <div className="search-results">
      <h3>Results for: <strong>{data.entity.id}</strong></h3>
      
      <EntityGraph
        entity={data.entity}
        relatedEntities={data.related_entities}
        links={data.links}
        onEntityClick={handleEntityClick}
      />
      
      <div className="articles-container">
        <h4>Related Articles ({data.articles.length})</h4>
        <div className="articles-grid">
          {data.articles.map((article) => (
            <ArticleCard 
              key={article._id}
              article={article}
              onClick={handleArticleClick}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default SearchResults;