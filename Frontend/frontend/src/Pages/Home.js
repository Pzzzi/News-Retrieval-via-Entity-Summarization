import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import SearchBar from '../Components/SearchBar';
import ArticleCard from '../Components/ArticleCard';
import '../styles/Home.css';

function Home() {
  const [query, setQuery] = useState('');
  const [homeData, setHomeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchHomeData = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/api/home-data');
        setHomeData(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHomeData();
  }, []);

  const handleSearch = (entity) => {
    navigate(`/search/${entity}`);
  };

  if (loading) return <div className="loading-spinner">Loading...</div>;
  if (error) return <div className="error-message">Error: {error}</div>;

  return (
    <div className="home-page">
      <section className="hero-section">
        <h1>🔍 Entity-Based News Search</h1>
        <SearchBar 
          query={query}
          setQuery={setQuery}
          onSearch={handleSearch}
        />
      </section>

      {homeData?.popular_entities?.length > 0 && (
        <section className="trending-section">
          <h2>Trending Entities</h2>
          <div className="entities-grid">
            {homeData.popular_entities.map((entity) => (
              <button
                key={entity.name}
                className="entity-chip"
                onClick={() => handleSearch(entity.name)}
              >
                {entity.name}
                <span className="count">{entity.count}</span>
              </button>
            ))}
          </div>
        </section>
      )}

      {homeData?.recent_articles?.length > 0 && (
        <section className="recent-articles">
          <h2>Latest News</h2>
          <div className="articles-grid">
            {homeData.recent_articles.map((article) => (
              <ArticleCard
                key={article._id}
                article={article}
                onClick={() => navigate(`/article/${article._id}`)}
              />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default Home;