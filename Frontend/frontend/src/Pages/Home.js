import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import SearchBar from '../Components/SearchBar';
import ArticleCard from '../Components/ArticleCard';

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

  if (loading) return (
    <div className="text-center py-10 text-xl">Loading...</div>
  );

  if (error) return (
    <div className="text-center py-10 text-xl text-red-600">Error: {error}</div>
  );

  return (
    <div className="max-w-[1200px] mx-auto p-5">
      {/* Hero Section */}
      <section className="text-center mb-10">
        <h1 className="text-4xl mb-5 text-blue-800 flex justify-center items-center gap-2">
          <span>🔍</span> Entity-Based News Search
        </h1>
        <SearchBar 
          query={query}
          setQuery={setQuery}
          onSearchSelect={handleSearch}
        />
      </section>

      {/* Trending Entities */}
      {homeData?.popular_entities?.length > 0 && (
        <section className="mb-10">
          <h2 className="text-2xl font-semibold border-b border-gray-200 pb-2 mb-5">
            Trending Entities
          </h2>
          <div className="flex flex-wrap gap-3">
            {homeData.popular_entities.map((entity) => (
              <button
                key={entity.name}
                className="bg-gray-100 hover:bg-gray-200 rounded-full px-4 py-2 
                           flex items-center gap-2 transition-all hover:-translate-y-0.5"
                onClick={() => handleSearch(entity.name)}
              >
                {entity.name}
                <span className="bg-blue-600 text-white rounded-full px-2 text-sm">
                  {entity.count}
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {/* Recent Articles */}
      {homeData?.recent_articles?.length > 0 && (
        <section>
          <h2 className="text-2xl font-semibold border-b border-gray-200 pb-2 mb-5">
            Latest News
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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