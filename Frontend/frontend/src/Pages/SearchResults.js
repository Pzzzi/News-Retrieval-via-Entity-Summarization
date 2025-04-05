import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import EntityGraph from '../Components/EntityGraph';
import ArticleList from '../Components/ArticleList';

function SearchResults() {
  const { entity } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const response = await axios.get(`http://127.0.0.1:5000/search?entity=${entity}`);
        setData(response.data);
      } catch (error) {
        console.error("Error fetching data:", error);
      }
      setLoading(false);
    };

    fetchData();
  }, [entity]);

  const handleEntityClick = (newEntity) => {
    navigate(`/search/${newEntity}`);
  };

  const handleArticleClick = (articleId) => {
    navigate(`/article/${articleId}`);
  };

  if (loading) return <p>Loading...</p>;
  if (!data) return <p>No data found for {entity}</p>;

  return (
    <div className="search-results">
      <h3>Results for: <strong>{data.entity.id}</strong></h3>
      
      <EntityGraph
        entity={data.entity}
        relatedEntities={data.related_entities}
        links={data.links}
        onEntityClick={handleEntityClick}
      />
      
      <div className="results-container">
        <ArticleList 
          articles={data.articles} 
          onArticleClick={handleArticleClick}
        />
      </div>
    </div>
  );
}

export default SearchResults;