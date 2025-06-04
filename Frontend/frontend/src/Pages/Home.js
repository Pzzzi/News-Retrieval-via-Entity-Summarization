import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ArticleCard from '../Components/ArticleCard';
import { debounce } from 'lodash';

function Home() {
  const [homeData, setHomeData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const navigate = useNavigate();

  // Initial load
  useEffect(() => {
    const fetchHomeData = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:5000/api/home-data');
        setHomeData(response.data);
        setArticles(response.data.recent_articles || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchHomeData();
  }, []);

  // Load more articles
  const loadMoreArticles = useCallback(async () => {
    if (!hasMore || isLoadingMore) return;

    setIsLoadingMore(true);
    try {
      const response = await axios.get(`http://127.0.0.1:5000/api/articles?page=${page + 1}`);
      const newArticles = response.data;

      if (newArticles.length === 0) {
        setHasMore(false);
      } else {
        setArticles(prev => [...prev, ...newArticles]);
        setPage(prev => prev + 1);
      }
    } catch (err) {
      console.error('Error loading more articles:', err);
    } finally {
      setIsLoadingMore(false);
    }
  }, [page, hasMore, isLoadingMore]);

  // Scroll handler with debounce
  useEffect(() => {
    const handleScroll = debounce(() => {
      const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
      // Load more when 80% scrolled
      if (scrollTop + clientHeight > scrollHeight * 0.8) {
        loadMoreArticles();
      }
    }, 100);

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadMoreArticles]);

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
    <div className="max-w-[1400px] mx-auto p-5">
      {/* Hero Section */}
      <section className="text-center mb-10">
        <h1 className="text-4xl mb-5 text-blue-800 flex justify-center items-center gap-2">
          Entity-Based News Retrieval
        </h1>
      </section>

      {/* Main Content with Sidebar */}
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Main Content (Latest News) */}
        <main className="lg:flex-1">
          <section>
            <h2 className="text-2xl font-semibold border-b border-gray-200 pb-2 mb-5">
              Latest News
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {articles.map((article) => (
                <ArticleCard
                  key={article._id}
                  article={{
                    ...article,
                    id: article._id,
                    entities: article.entities.map(e => ({
                      name: e.normalized_label,
                      type: e.type
                    }))
                  }}
                  onClick={() => navigate(`/article/${article._id}`)}
                  onEntityClick={(entity) => {
                    const label = entity.name || entity.normalized_label || entity.text;
                    navigate(`/search/${encodeURIComponent(label)}`);
                  }}
                />
              ))}
            </div>
            {isLoadingMore && (
              <div className="text-center py-5">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
              </div>
            )}
            {!hasMore && (
              <div className="text-center py-5 text-gray-500">
                No more articles to load
              </div>
            )}
          </section>
        </main>

        {/* Sidebar (Trending Entities) */}
        <aside className="lg:w-80 xl:w-96">
          <div className="sticky top-5 max-h-[calc(100vh-2.5rem)] overflow-y-auto">
            {homeData?.popular_entities?.length > 0 && (
              <section className="sticky top-5">
                <h2 className="text-2xl font-semibold border-b border-gray-200 pb-2 mb-5">
                  Trending Entities
                </h2>
                <div className="space-y-4 pb-4">
                  {homeData.popular_entities.map((entity) => {
                    // Define colors based on entity type
                    let bgColor, iconColor;

                    switch (entity.type) {
                      case 'PERSON':
                        bgColor = 'bg-blue-50';
                        iconColor = 'text-blue-600';
                        break;
                      case 'NORP':
                        bgColor = 'bg-purple-50';
                        iconColor = 'text-purple-600';
                        break;
                      case 'FAC':
                        bgColor = 'bg-amber-50';
                        iconColor = 'text-amber-600';
                        break;
                      case 'ORG':
                        bgColor = 'bg-rose-50';
                        iconColor = 'text-rose-600';
                        break;
                      case 'GPE':
                        bgColor = 'bg-green-50';
                        iconColor = 'text-green-600';
                        break;
                      case 'LOC':
                        bgColor = 'bg-emerald-50';
                        iconColor = 'text-emerald-600';
                        break;
                      case 'PRODUCT':
                        bgColor = 'bg-cyan-50';
                        iconColor = 'text-cyan-600';
                        break;
                      case 'EVENT':
                        bgColor = 'bg-red-50';
                        iconColor = 'text-red-600';
                        break;
                      case 'WORK_OF_ART':
                        bgColor = 'bg-fuchsia-50';
                        iconColor = 'text-fuchsia-600';
                        break;
                      case 'LAW':
                        bgColor = 'bg-violet-50';
                        iconColor = 'text-violet-600';
                        break;
                      case 'LANGUAGE':
                        bgColor = 'bg-sky-50';
                        iconColor = 'text-sky-600';
                        break;
                      case 'DATE':
                        bgColor = 'bg-yellow-50';
                        iconColor = 'text-yellow-600';
                        break;
                      case 'TIME':
                        bgColor = 'bg-orange-50';
                        iconColor = 'text-orange-600';
                        break;
                      case 'PERCENT':
                        bgColor = 'bg-lime-50';
                        iconColor = 'text-lime-600';
                        break;
                      case 'MONEY':
                        bgColor = 'bg-teal-50';
                        iconColor = 'text-teal-600';
                        break;
                      case 'QUANTITY':
                        bgColor = 'bg-pink-50';
                        iconColor = 'text-pink-600';
                        break;
                      case 'ORDINAL':
                        bgColor = 'bg-indigo-50';
                        iconColor = 'text-indigo-600';
                        break;
                      case 'CARDINAL':
                        bgColor = 'bg-amber-50';
                        iconColor = 'text-amber-600';
                        break;
                      default:
                        bgColor = 'bg-gray-50';
                        iconColor = 'text-gray-600';
                    }

                    // Get icon component based on entity type
                    const getEntityIcon = () => {
                      switch (entity.type) {
                        case 'PERSON':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                          );
                        case 'ORG':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                          );
                        case 'GPE':
                        case 'LOC':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                          );
                        case 'FAC':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                          );
                        case 'PRODUCT':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                            </svg>
                          );
                        case 'EVENT':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                          );
                        case 'WORK_OF_ART':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                            </svg>
                          );
                        case 'LAW':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                          );
                        case 'LANGUAGE':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                            </svg>
                          );
                        case 'DATE':
                        case 'TIME':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          );
                        case 'MONEY':
                        case 'PERCENT':
                        case 'QUANTITY':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          );
                        case 'ORDINAL':
                        case 'CARDINAL':
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                            </svg>
                          );
                        default:
                          return (
                            <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                          );
                      }
                    };

                    return (
                      <div
                        key={`${entity.rank}-${entity.normalized_label || 'unknown'}`}
                        className={`border border-gray-200 rounded-xl p-4 ${bgColor} shadow-sm hover:shadow-md transition cursor-pointer`}
                        onClick={() =>
                          entity.normalized_label && handleSearch(entity.normalized_label)
                        }
                      >
                        <div className="flex items-start gap-3 mb-2">
                          <div className={`flex-shrink-0 ${bgColor.replace('50', '100')} rounded-md p-2`}>
                            {getEntityIcon()}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between">
                              <h3 className="text-lg font-semibold text-gray-900">
                                {entity.normalized_label || <span className="italic text-gray-400">Unnamed Entity</span>}
                              </h3>
                              <span className="bg-gray-600 text-white text-xs rounded-full px-2 py-0.5">
                                #{entity.rank}
                              </span>
                            </div>
                            <p className="text-sm text-gray-600 mb-2">
                              {entity.description || "No description available."}
                            </p>
                            <div className="text-xs text-gray-500 flex justify-between">
                              <span>Type: {entity.type}</span>
                              <span>Mentions: {entity.count}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}

export default Home;