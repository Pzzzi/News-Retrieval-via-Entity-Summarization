import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import EntityGraph from '../Components/EntityGraph';
import ArticleCard from '../Components/ArticleCard';
import { debounce } from 'lodash';

function SearchResults() {
  const { entity } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [isLoadingMore, setIsLoadingMore] = useState(false);

  // Initial data load
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.get(
          `http://127.0.0.1:5000/search?entity=${entity}`,
          { timeout: 10000 }
        );

        if (!response.data?.entity) {
          throw new Error('Invalid API response structure');
        }

        setData(response.data);
        setHasMore(response.data.pagination?.has_more || false);
      } catch (error) {
        console.error("Error fetching data:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [entity]);

  // Load more articles
  const loadMoreArticles = useCallback(async () => {
    if (!hasMore || isLoadingMore) return;

    setIsLoadingMore(true);
    try {
      const nextPage = page + 1;
      const response = await axios.get(
        `http://127.0.0.1:5000/search?entity=${entity}&page=${nextPage}`,
        { timeout: 10000 }
      );

      if (response.data?.articles?.length) {
        setData(prev => ({
          ...prev,
          articles: [...prev.articles, ...response.data.articles],
          pagination: response.data.pagination
        }));
        setPage(nextPage);
        setHasMore(response.data.pagination?.has_more || false);
      } else {
        setHasMore(false);
      }
    } catch (error) {
      console.error("Error loading more articles:", error);
    } finally {
      setIsLoadingMore(false);
    }
  }, [entity, page, hasMore, isLoadingMore]);

  // Scroll handler
  useEffect(() => {
    const handleScroll = debounce(() => {
      const { scrollTop, scrollHeight, clientHeight } = document.documentElement;
      if (scrollTop + clientHeight > scrollHeight * 0.8) {
        loadMoreArticles();
      }
    }, 100);

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [loadMoreArticles]);

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

  const handleEntityClick = (entity) => {
    const label = entity.name || entity.normalized_label || entity.text;
    navigate(`/search/${encodeURIComponent(label)}`);
  };

  const handleArticleClick = (articleId) => {
    navigate(`/article/${articleId}`);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
        <div className="flex flex-col items-center justify-center min-h-[60vh] px-4">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
            <div className="absolute inset-0 w-16 h-16 border-4 border-transparent border-r-indigo-400 rounded-full animate-spin animate-reverse" style={{ animationDelay: '0.15s' }}></div>
          </div>
          <div className="mt-8 text-center">
            <h2 className="text-2xl font-bold text-slate-800 mb-2">Discovering Insights</h2>
            <p className="text-lg text-slate-600">
              Searching for <span className="font-semibold text-blue-600 px-2 py-1 bg-blue-100 rounded-lg">"{entity}"</span>
            </p>
            <div className="mt-4 flex space-x-1 justify-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 flex items-center justify-center px-4">
        <div className="max-w-md w-full">
          <div className="bg-white rounded-3xl shadow-2xl p-8 text-center border border-red-100">
            <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-orange-500 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-3">Something Went Wrong</h3>
            <p className="text-slate-600 mb-6 leading-relaxed">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="w-full bg-gradient-to-r from-red-500 to-orange-500 text-white font-semibold py-3 px-6 rounded-xl hover:from-red-600 hover:to-orange-600 transform hover:scale-105 transition-all duration-200 shadow-lg hover:shadow-xl"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!data || !data.articles?.length) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-purple-50 to-pink-50 flex items-center justify-center px-4">
        <div className="max-w-lg w-full text-center">
          <div className="bg-white rounded-3xl shadow-2xl p-10 border border-purple-100">
            <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center mx-auto mb-8">
              <svg className="w-12 h-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-4">No Results Found</h3>
            <p className="text-slate-600 mb-2">
              We couldn't find any articles for
            </p>
            <p className="text-lg font-semibold text-purple-600 bg-purple-100 px-4 py-2 rounded-xl inline-block mb-6">
              "{entity}"
            </p>
            <p className="text-slate-500">Try searching with different keywords or check your spelling</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-12 max-w-7xl">

        {/* Header Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-indigo-600 bg-clip-text text-transparent mb-4">
            Research Hub
          </h1>
          <p className="text-xl text-slate-600">
            Exploring insights for <span className="font-semibold text-blue-600">"{entity}"</span>
          </p>
        </div>

        <div className="space-y-8">
          {/* Entity Summary Section */}
          {summaryLoading ? (
            <div className="bg-white/70 backdrop-blur-sm rounded-3xl p-8 border border-blue-200 shadow-lg">
              <div className="flex items-center space-x-4">
                <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gradient-to-r from-blue-200 to-purple-200 rounded-full animate-pulse mb-3"></div>
                  <div className="h-3 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full animate-pulse w-3/4"></div>
                </div>
              </div>
              <p className="text-slate-700 mt-4 font-medium">
                Generating AI-powered summary for <strong className="text-blue-600">{data.entity.id}</strong>...
              </p>
            </div>
          ) : summary ? (
            <div className="bg-white/80 backdrop-blur-sm rounded-3xl p-8 border border-blue-200 shadow-xl hover:shadow-2xl transition-all duration-300">
              <div className="flex items-start space-x-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center flex-shrink-0">
                  <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div className="flex-1">
                  <h4 className="text-2xl font-bold text-slate-800 mb-2">
                    Current Insights
                  </h4>
                  <p className="text-slate-600">
                    AI-generated summary for <span className="font-semibold text-blue-600">{data.entity.id}</span>
                  </p>
                </div>
              </div>
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-6 border border-blue-100">
                <p className="text-slate-700 leading-relaxed text-lg">{summary}</p>
              </div>
            </div>
          ) : null}

          {/* Entity Graph Section */}
          <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-blue-200 overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-purple-600 p-6">
              <h4 className="text-2xl font-bold text-white text-center flex items-center justify-center space-x-3">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>Relationship Network</span>
              </h4>
              <p className="text-blue-100 text-center mt-2">
                Interactive visualization for <span className="font-semibold text-white">{data.entity.id}</span>
              </p>
            </div>
            <div className="p-8 bg-gradient-to-br from-white to-blue-50">
              <div className="w-full overflow-x-auto">
                <div className="mx-auto" style={{ width: 'fit-content' }}>
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
        </div>

        {/* Articles Section */}
        <div className="mt-16">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h4 className="text-3xl font-bold text-slate-800 mb-2">
                Related Articles
              </h4>
              <p className="text-slate-600 text-lg">
                <span className="inline-flex items-center space-x-2 bg-white/80 backdrop-blur-sm px-4 py-2 rounded-full border border-blue-200">
                  <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="font-semibold text-blue-600">
                    {data.pagination?.total || data.articles.length} articles found
                  </span>
                </span>
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {data.articles.map((article) => (
              <ArticleCard
                key={article._id}
                article={article}
                onClick={handleArticleClick}
                onEntityClick={handleEntityClick}
              />
            ))}
          </div>

          {/* Loading indicator */}
          {isLoadingMore && (
            <div className="flex justify-center my-12">
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-lg border border-blue-200">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin"></div>
                  <p className="text-slate-700 font-medium">Loading more articles...</p>
                </div>
              </div>
            </div>
          )}

          {/* No more articles message */}
          {!hasMore && data.articles.length > 0 && (
            <div className="text-center py-12">
              <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 max-w-md mx-auto border border-slate-200">
                <svg className="w-8 h-8 text-slate-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <p className="text-slate-600 font-medium">All articles loaded</p>
                <p className="text-slate-500 text-sm mt-1">You've reached the end of the results</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default SearchResults;
