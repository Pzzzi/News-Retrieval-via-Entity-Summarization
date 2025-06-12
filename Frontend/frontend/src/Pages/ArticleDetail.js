import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

function ArticleDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [articleData, setArticleData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeImage, setActiveImage] = useState(0);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await axios.get(`http://127.0.0.1:5000/article_summary/${id}`);

        if (response.data.error) {
          throw new Error(response.data.error);
        }

        setArticleData(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [id]);

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="text-center">
        <div className="relative inline-block">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-transparent bg-gradient-to-r from-blue-500 to-purple-600 mx-auto mb-6"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-white rounded-full"></div>
        </div>
        <div className="backdrop-blur-sm bg-white/80 rounded-2xl p-6 shadow-xl border border-white/20">
          <h2 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            Generating summary...
          </h2>
          <p className="mt-2 text-slate-600">This may take a few moments</p>
        </div>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 via-pink-50 to-rose-100 flex items-center justify-center p-4">
      <div className="text-center max-w-md">
        <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-r from-red-500 to-pink-500 mb-6 shadow-lg">
          <svg className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="backdrop-blur-sm bg-white/90 rounded-2xl p-8 shadow-xl border border-white/20">
          <h3 className="text-xl font-semibold text-slate-900 mb-3">Error loading article</h3>
          <p className="text-slate-600 mb-8 leading-relaxed">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="group relative px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-medium rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200"
          >
            <span className="relative z-10">Back to results</span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-700 to-purple-700 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      </div>

      <div className="backdrop-blur-sm bg-white/80 shadow-2xl border border-white/20 rounded-3xl mb-8 overflow-hidden">
        <div className="relative px-8 py-8 bg-gradient-to-r from-blue-600/10 to-purple-600/10 border-b border-white/20">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 to-purple-600/5"></div>
          <div className="relative">
            <h1 className="text-3xl font-bold leading-tight text-slate-900 mb-3">
              {articleData?.article_title}
            </h1>
            <div className="flex items-center text-slate-600">
              <div className="p-2 rounded-full bg-white/70 mr-3">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <span className="font-medium">Published: {formatDate(articleData?.date)}</span>
            </div>
          </div>
        </div>

        {/* Article Images Gallery */}
        {articleData?.images?.length > 0 && (
          <div className="px-8 py-8">
            <div className="relative h-80 sm:h-96 rounded-2xl overflow-hidden mb-6 shadow-xl">
              <img
                src={articleData.images[activeImage]}
                alt="Article visual"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
            </div>
            {articleData.images.length > 1 && (
              <div className="flex space-x-3 overflow-x-auto py-2">
                {articleData.images.map((img, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveImage(index)}
                    className={`flex-shrink-0 w-20 h-20 rounded-xl overflow-hidden transition-all duration-200 ${activeImage === index
                      ? 'ring-4 ring-blue-500 ring-offset-2 ring-offset-white/80 scale-105 shadow-lg'
                      : 'hover:scale-105 shadow-md hover:shadow-lg'
                      }`}
                  >
                    <img
                      src={img}
                      alt={`Thumbnail ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Summary Section */}
        <div className="px-8 py-8 border-t border-white/20">
          <div className="flex items-center mb-6">
            <div className="p-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 mr-4">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Article Summary</h2>
          </div>
          <div className="prose max-w-none">
            {articleData?.summary ? (
              <div className="text-slate-700 leading-relaxed text-lg backdrop-blur-sm bg-white/50 rounded-2xl p-6 border border-white/20">
                <p className="whitespace-pre-line">{articleData.summary}</p>
              </div>
            ) : (
              <p className="text-slate-500 italic text-center py-8">No summary available for this article</p>
            )}
          </div>
        </div>

        {/* Entities Section */}
        {articleData?.entities?.length > 0 && (
          <div className="px-8 py-8 border-t border-white/20">
            <div className="flex items-center mb-6">
              <div className="p-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 mr-4">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a1.994 1.994 0 01-1.414.586H7a1 1 0 01-1-1V3a1 1 0 011-1z" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Key Entities Mentioned</h2>
            </div>
            <div className="relative">
              <div className="flex space-x-4 pb-4 overflow-x-auto scrollbar-hide">
                {articleData.entities.map((entity, index) => {
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
                      bgColor = 'bg-gray-50/80';
                      iconColor = 'text-gray-600';
                      gradientFrom = 'from-gray-500';
                      gradientTo = 'to-gray-600';
                  }

                  const getEntityIcon = () => {
                    switch (entity.type) {
                      case 'PERSON':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                        );
                      case 'ORG':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                          </svg>
                        );
                      case 'GPE':
                      case 'LOC':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        );
                      case 'FAC':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                          </svg>
                        );
                      case 'PRODUCT':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                          </svg>
                        );
                      case 'EVENT':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        );
                      case 'WORK_OF_ART':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                          </svg>
                        );
                      case 'LAW':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                          </svg>
                        );
                      case 'LANGUAGE':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                          </svg>
                        );
                      case 'DATE':
                      case 'TIME':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        );
                      case 'MONEY':
                      case 'PERCENT':
                      case 'QUANTITY':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        );
                      case 'ORDINAL':
                      case 'CARDINAL':
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                          </svg>
                        );
                      default:
                        return (
                          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        );
                    }
                  };

                  return (
                    <div key={index} className={`${bgColor} backdrop-blur-sm p-4 rounded-2xl border border-white/20 shadow-lg hover:shadow-xl transition-all duration-200 hover:-translate-y-1`} style={{ minWidth: '220px' }}>
                      <div className="flex items-start">
                        <div className={`flex-shrink-0 p-3 rounded-xl bg-gradient-to-r ${gradientFrom} ${gradientTo} shadow-lg`}>
                          {getEntityIcon()}
                        </div>
                        <div className="ml-4">
                          <h3 className="text-sm font-semibold text-slate-900 mb-1">{entity.label}</h3>
                          <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${bgColor} ${iconColor} border border-current/20`}>
                            {entity.type}
                          </div>
                          {entity.description && (
                            <p className="text-xs text-slate-600 mt-2 leading-relaxed">{entity.description}</p>
                          )}
                          {entity.wikidata_url && (
                            <a
                              href={entity.wikidata_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center text-xs text-blue-600 hover:text-blue-700 mt-2 font-medium transition-colors duration-200"
                            >
                              More info
                              <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Article Link */}
        <div className="px-8 py-6 bg-gradient-to-r from-slate-50/50 to-blue-50/50 border-t border-white/20">
          <div className="flex justify-end">
            <a
              href={articleData?.article_url}
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-all duration-200"
            >
              <span className="relative z-10">Read full article on Sky News</span>
              <svg className="ml-2 -mr-1 w-5 h-5 group-hover:translate-x-1 transition-transform duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
              <div className="absolute inset-0 bg-gradient-to-r from-blue-700 to-purple-700 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
            </a>
          </div>
        </div>
      </div>

      {/* Additional Metadata */}
      <div className="bg-white shadow overflow-hidden sm:rounded-lg">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h3 className="text-lg font-medium leading-6 text-gray-900">Article Metadata</h3>
        </div>
        <div className="px-4 py-5 sm:p-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-8 sm:grid-cols-2">
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Article ID</dt>
              <dd className="mt-1 text-sm text-gray-900 break-all">{articleData?.article_id}</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Source</dt>
              <dd className="mt-1 text-sm text-gray-900">Sky News</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Published Date</dt>
              <dd className="mt-1 text-sm text-gray-900">{formatDate(articleData?.date)}</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500">Images Available</dt>
              <dd className="mt-1 text-sm text-gray-900">{articleData?.images?.length || 0}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  );
}

export default ArticleDetail;
