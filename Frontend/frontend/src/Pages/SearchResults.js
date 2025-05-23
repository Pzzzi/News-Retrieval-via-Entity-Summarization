import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import EntityGraph from '../Components/EntityGraph';
import ArticleCard from '../Components/ArticleCard';

function SearchResults() {
  const { entity } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch entity search results
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(
          `http://127.0.0.1:5000/search?entity=${entity}`,
          { timeout: 10000 }
        );

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

  // Fetch entity summary from titles
  useEffect(() => {
    const fetchSummary = async () => {
      setSummaryLoading(true);
      try {
        const response = await axios.get(
          `http://127.0.0.1:5000/entity_summary_titles/${entity}`,
          { timeout: 30000 }
        );
  
        if (response.data?.summary) {
          setSummary(response.data.summary);
        }
      } catch (err) {
        console.warn("No summary found or error fetching summary:", err);
        setSummary(prev => prev ?? null);
      } finally {
        setSummaryLoading(false);
      }
    };
  
    fetchSummary();
  }, [entity]);  

  const handleEntityClick = (newEntity) => {
    navigate(`/search/${newEntity}`);
  };

  const handleArticleClick = (articleId) => {
    navigate(`/article/${articleId}`);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-lg text-gray-700">Loading results for "<span className="font-semibold">{entity}"</span>...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] text-center p-6">
        <div className="text-red-500 mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-lg font-medium text-gray-800 mb-2">Error loading results</p>
        <p className="text-gray-600 mb-4">{error}</p>
        <button 
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (!data || !data.articles?.length) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[300px] text-center p-6">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-lg font-medium text-gray-800 mb-1">No articles found for "<span className="font-semibold">{entity}"</span></p>
        <p className="text-gray-600">Try searching for something else</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        {/* Entity Summary Section */}
        {summaryLoading ? (
          <div className="bg-blue-50 rounded-lg p-4 mb-6 animate-pulse">
            <p className="text-gray-700">
              Generating summary for <strong>{data.entity.id}</strong>...
            </p>
          </div>
        ) : summary ? (
          <div className="bg-gray-50 rounded-lg p-6 mb-6 border border-gray-200">
            <h4 className="text-lg font-semibold text-gray-800 mb-3">
              Things on-going for <span className="text-blue-600">{data.entity.id}</span>
            </h4>
            <p className="text-gray-700 leading-relaxed">{summary}</p>
          </div>
        ) : null}

        <div className="mb-8">
          <div className="bg-white rounded-2xl shadow-md p-6 border border-gray-200">
            <h4 className="text-lg font-semibold text-gray-800 mb-4 text-center">
              Relationship Graph for <span className="text-blue-600">{data.entity.id}</span>
            </h4>
            <div className="flex justify-center">
              <EntityGraph
                entity={data.entity}
                relatedEntities={data.related_entities}
                links={data.links}
                onEntityClick={handleEntityClick}
              />
            </div>
          </div>
        </div>
      </div>
      
      <div className="mb-8">
        <h4 className="text-xl font-semibold text-gray-800 mb-4">
          Related Articles ({data.articles.length})
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.articles.map((article) => (
            <ArticleCard 
              key={article._id}
              article={article}
              onClick={handleArticleClick}
              onEntityClick={handleEntityClick}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

export default SearchResults;
