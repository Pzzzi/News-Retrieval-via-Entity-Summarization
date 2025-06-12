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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="text-center space-y-4">
        <div className="relative w-16 h-16 mx-auto">
          <div className="absolute inset-0 rounded-full border-4 border-indigo-100/80"></div>
          <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
        </div>
        <div className="space-y-1">
          <p className="text-slate-600 font-medium">Loading latest content...</p>
          <p className="text-sm text-slate-500">This will just take a moment</p>
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-rose-50 to-pink-100 flex items-center justify-center">
      <div className="text-center bg-white rounded-2xl shadow-xl p-8 max-w-md mx-4">
        <div className="w-16 h-16 mx-auto mb-4 bg-red-100 rounded-full flex items-center justify-center">
          <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Oops! Something went wrong</h2>
        <p className="text-gray-600">{error}</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="max-w-[1400px] mx-auto px-6 py-8">
        {/* Hero Section */}
        <section className="text-center mb-20 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-indigo-600/10 to-purple-600/10 rounded-3xl"></div>
          <div className="absolute inset-0 bg-white/20 backdrop-blur-sm rounded-3xl"></div>
          <div className="relative max-w-5xl mx-auto py-16 px-8">
            <div className="mb-6">
              <div className="inline-flex items-center px-4 py-2 bg-white/80 backdrop-blur-sm rounded-full text-sm font-medium text-indigo-700 border border-indigo-200/50 shadow-sm">
                <div className="w-2 h-2 bg-indigo-500 rounded-full mr-2 animate-pulse"></div>
                Live Updates
              </div>
            </div>
            <h1 className="font-black text-6xl md:text-7xl lg:text-8xl mb-6 text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-purple-600 to-blue-600 leading-none tracking-tight">
              What's Popular Now
            </h1>
            <p className="text-xl md:text-2xl text-slate-600 font-medium max-w-3xl mx-auto leading-relaxed">
              Discover the latest trending content and stay ahead of the conversation
            </p>
            <div className="mt-8 flex justify-center">
              <div className="w-24 h-1 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"></div>
            </div>
          </div>
        </section>

        {/* Main Content with Sidebar */}
        <div className="flex flex-col xl:flex-row gap-12">
          {/* Main Content (Latest News) */}
          <main className="xl:flex-1">
            <section className="bg-white/60 backdrop-blur-sm rounded-3xl p-8 shadow-xl border border-white/20">
              <div className="flex items-center gap-4 mb-8">
                <div className="w-12 h-12 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center shadow-lg">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-3xl font-bold text-slate-800">Latest News</h2>
                  <p className="text-slate-600">Fresh stories as they happen</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
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
                <div className="text-center py-12">
                  <div className="relative w-12 h-12 mx-auto mb-4">
                    <div className="absolute inset-0 rounded-full border-4 border-indigo-100"></div>
                    <div className="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
                  </div>
                  <p className="text-slate-600 font-medium">Loading more articles...</p>
                </div>
              )}

              {!hasMore && (
                <div className="text-center py-12">
                  <div className="w-16 h-16 mx-auto mb-4 bg-slate-100 rounded-full flex items-center justify-center">
                    <svg className="w-8 h-8 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <p className="text-slate-500 font-medium">You're all caught up!</p>
                  <p className="text-slate-400 text-sm">No more articles to load</p>
                </div>
              )}
            </section>
          </main>

          {/* Sidebar (Trending Entities) */}
          <aside className="xl:w-96">
            <div className="sticky top-8">
              {homeData?.popular_entities?.length > 0 && (
                <section className="bg-white/60 backdrop-blur-sm rounded-3xl p-8 shadow-xl border border-white/20">
                  <div className="flex items-center gap-4 mb-8">
                    <div className="w-12 h-12 bg-gradient-to-r from-rose-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-4 4" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-slate-800">Trending</h2>
                      <p className="text-slate-600">What everyone's talking about</p>
                    </div>
                  </div>

                  <div className="space-y-4 max-h-[calc(100vh-12rem)] overflow-y-auto pr-2">
                    {homeData.popular_entities.map((entity) => {
                      // Define colors based on entity type
                      let bgColor, iconColor, gradientFrom, gradientTo;

                      switch (entity.type) {
                        case 'PERSON':
                          bgColor = 'bg-blue-50/80';
                          iconColor = 'text-blue-600';
                          gradientFrom = 'from-blue-500';
                          gradientTo = 'to-blue-600';
                          break;
                        case 'NORP':
                          bgColor = 'bg-purple-50/80';
                          iconColor = 'text-purple-600';
                          gradientFrom = 'from-purple-500';
                          gradientTo = 'to-purple-600';
                          break;
                        case 'FAC':
                          bgColor = 'bg-amber-50/80';
                          iconColor = 'text-amber-600';
                          gradientFrom = 'from-amber-500';
                          gradientTo = 'to-amber-600';
                          break;
                        case 'ORG':
                          bgColor = 'bg-rose-50/80';
                          iconColor = 'text-rose-600';
                          gradientFrom = 'from-rose-500';
                          gradientTo = 'to-rose-600';
                          break;
                        case 'GPE':
                          bgColor = 'bg-green-50/80';
                          iconColor = 'text-green-600';
                          gradientFrom = 'from-green-500';
                          gradientTo = 'to-green-600';
                          break;
                        case 'LOC':
                          bgColor = 'bg-emerald-50/80';
                          iconColor = 'text-emerald-600';
                          gradientFrom = 'from-emerald-500';
                          gradientTo = 'to-emerald-600';
                          break;
                        case 'PRODUCT':
                          bgColor = 'bg-cyan-50/80';
                          iconColor = 'text-cyan-600';
                          gradientFrom = 'from-cyan-500';
                          gradientTo = 'to-cyan-600';
                          break;
                        case 'EVENT':
                          bgColor = 'bg-red-50/80';
                          iconColor = 'text-red-600';
                          gradientFrom = 'from-red-500';
                          gradientTo = 'to-red-600';
                          break;
                        case 'WORK_OF_ART':
                          bgColor = 'bg-fuchsia-50/80';
                          iconColor = 'text-fuchsia-600';
                          gradientFrom = 'from-fuchsia-500';
                          gradientTo = 'to-fuchsia-600';
                          break;
                        case 'LAW':
                          bgColor = 'bg-violet-50/80';
                          iconColor = 'text-violet-600';
                          gradientFrom = 'from-violet-500';
                          gradientTo = 'to-violet-600';
                          break;
                        case 'LANGUAGE':
                          bgColor = 'bg-sky-50/80';
                          iconColor = 'text-sky-600';
                          gradientFrom = 'from-sky-500';
                          gradientTo = 'to-sky-600';
                          break;
                        case 'DATE':
                          bgColor = 'bg-yellow-50/80';
                          iconColor = 'text-yellow-600';
                          gradientFrom = 'from-yellow-500';
                          gradientTo = 'to-yellow-600';
                          break;
                        case 'TIME':
                          bgColor = 'bg-orange-50/80';
                          iconColor = 'text-orange-600';
                          gradientFrom = 'from-orange-500';
                          gradientTo = 'to-orange-600';
                          break;
                        case 'PERCENT':
                          bgColor = 'bg-lime-50/80';
                          iconColor = 'text-lime-600';
                          gradientFrom = 'from-lime-500';
                          gradientTo = 'to-lime-600';
                          break;
                        case 'MONEY':
                          bgColor = 'bg-teal-50/80';
                          iconColor = 'text-teal-600';
                          gradientFrom = 'from-teal-500';
                          gradientTo = 'to-teal-600';
                          break;
                        case 'QUANTITY':
                          bgColor = 'bg-pink-50/80';
                          iconColor = 'text-pink-600';
                          gradientFrom = 'from-pink-500';
                          gradientTo = 'to-pink-600';
                          break;
                        case 'ORDINAL':
                          bgColor = 'bg-indigo-50/80';
                          iconColor = 'text-indigo-600';
                          gradientFrom = 'from-indigo-500';
                          gradientTo = 'to-indigo-600';
                          break;
                        case 'CARDINAL':
                          bgColor = 'bg-amber-50/80';
                          iconColor = 'text-amber-600';
                          gradientFrom = 'from-amber-500';
                          gradientTo = 'to-amber-600';
                          break;
                        default:
                          bgColor = 'bg-slate-50/80';
                          iconColor = 'text-slate-600';
                          gradientFrom = 'from-slate-500';
                          gradientTo = 'to-slate-600';
                      }

                      // Get icon component based on entity type
                      const getEntityIcon = () => {
                        switch (entity.type) {
                          case 'PERSON':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                              </svg>
                            );
                          case 'ORG':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                              </svg>
                            );
                          case 'GPE':
                          case 'LOC':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                              </svg>
                            );
                          case 'FAC':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                              </svg>
                            );
                          case 'PRODUCT':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                              </svg>
                            );
                          case 'EVENT':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                            );
                          case 'WORK_OF_ART':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                              </svg>
                            );
                          case 'LAW':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                              </svg>
                            );
                          case 'LANGUAGE':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                              </svg>
                            );
                          case 'DATE':
                          case 'TIME':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            );
                          case 'MONEY':
                          case 'PERCENT':
                          case 'QUANTITY':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            );
                          case 'ORDINAL':
                          case 'CARDINAL':
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                            );
                          default:
                            return (
                              <svg className={`h-5 w-5 ${iconColor}`} fill="none" stroke="white" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            );
                        }
                      };

                      return (
                        <div
                          key={`${entity.rank}-${entity.normalized_label || 'unknown'}`}
                          className={`group relative ${bgColor} backdrop-blur-sm border border-white/20 rounded-2xl p-5 shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer hover:scale-[1.02] overflow-hidden`}
                          onClick={() =>
                            entity.normalized_label && handleSearch(entity.normalized_label)
                          }
                        >
                          <div className="absolute top-0 right-0 w-32 h-32 opacity-10 transform translate-x-8 -translate-y-8">
                            <div className={`w-full h-full bg-gradient-to-br ${gradientFrom} ${gradientTo} rounded-full blur-2xl`}></div>
                          </div>

                          <div className="relative flex items-start gap-4">
                            <div className={`flex-shrink-0 w-12 h-12 bg-gradient-to-br ${gradientFrom} ${gradientTo} rounded-xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                              <div className="w-6 h-6 text-white">
                                {getEntityIcon()}
                              </div>
                            </div>

                            <div className="flex-1 min-w-0">
                              <div className="flex items-start justify-between mb-3">
                                <h3 className="text-lg font-bold text-slate-800 group-hover:text-slate-900 transition-colors truncate pr-2">
                                  {entity.normalized_label || <span className="italic text-slate-400">Unnamed Entity</span>}
                                </h3>
                                <div className={`flex-shrink-0 px-3 py-1 bg-gradient-to-r ${gradientFrom} ${gradientTo} text-white text-xs font-bold rounded-full shadow-sm`}>
                                  #{entity.rank}
                                </div>
                              </div>

                              <p className="text-sm text-slate-600 mb-4 line-clamp-2 leading-relaxed">
                                {entity.description || "No description available."}
                              </p>

                              <div className="flex items-center justify-between text-xs">
                                <span className="px-2 py-1 bg-white/60 backdrop-blur-sm rounded-md text-slate-700 font-medium border border-white/20">
                                  {entity.type}
                                </span>
                                <span className="text-slate-500 font-medium">
                                  {entity.count} mentions
                                </span>
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
    </div>
  );
}

export default Home;