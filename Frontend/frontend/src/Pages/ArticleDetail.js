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
    <div className="flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <h2 className="text-lg font-medium text-gray-900">Generating summary...</h2>
        <p className="mt-1 text-gray-500">This may take a few moments</p>
      </div>
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-screen py-12 px-4 sm:px-6 lg:px-8">
      <div className="text-center max-w-md">
        <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
          <svg className="h-6 w-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Error loading article</h3>
        <p className="text-gray-600 mb-6">{error}</p>
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Back to results
        </button>
      </div>
    </div>
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center text-blue-600 hover:text-blue-800 mb-6 transition-colors"
      >
        <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to results
      </button>

      <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-8">
        <div className="px-4 py-5 sm:px-6 border-b border-gray-200">
          <h1 className="text-2xl font-bold leading-6 text-gray-900">
            {articleData?.article_title}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Published: {formatDate(articleData?.date)}
          </p>
        </div>

        {/* Article Images Gallery */}
        {articleData?.images?.length > 0 && (
          <div className="px-4 py-5 sm:p-6 border-b border-gray-200">
            <div className="relative h-64 sm:h-96 rounded-lg overflow-hidden mb-4">
              <img
                src={articleData.images[activeImage]}
                alt="Article visual"
                className="w-full h-full object-cover"
              />
            </div>
            {articleData.images.length > 1 && (
              <div className="flex space-x-2 overflow-x-auto py-2">
                {articleData.images.map((img, index) => (
                  <button
                    key={index}
                    onClick={() => setActiveImage(index)}
                    className={`flex-shrink-0 w-16 h-16 rounded-md overflow-hidden ${activeImage === index ? 'ring-2 ring-blue-500' : ''}`}
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
        <div className="px-4 py-5 sm:p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Article Summary</h2>
          <div className="prose max-w-none text-gray-700">
            {articleData?.summary ? (
              <p className="whitespace-pre-line">{articleData.summary}</p>
            ) : (
              <p className="text-gray-500 italic">No summary available for this article</p>
            )}
          </div>
        </div>

        {/* Entities Section */}
        {articleData?.entities?.length > 0 && (
          <div className="px-4 py-5 sm:p-6 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Key Entities Mentioned</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {articleData.entities.map((entity, index) => {
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
                    bgColor = 'bg-indigo-50';
                    iconColor = 'text-indigo-600';
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
                    bgColor = 'bg-rose-50';
                    iconColor = 'text-rose-600';
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
                  <div key={index} className={`${bgColor} p-3 rounded-md`}>
                    <div className="flex items-start">
                      <div className={`flex-shrink-0 ${bgColor.replace('50', '100')} rounded-md p-2`}>
                        {getEntityIcon()}
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-gray-900">{entity.label}</h3>
                        <p className="text-xs text-gray-500">{entity.type}</p>
                        {entity.description && (
                          <p className="text-xs text-gray-600 mt-1">{entity.description}</p>
                        )}
                        {entity.wikidata_url && (
                          <a
                            href={entity.wikidata_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline mt-1 inline-block"
                          >
                            More info
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Article Link */}
        <div className="px-4 py-4 sm:px-6 bg-gray-50 text-right">
          <a
            href={articleData?.article_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Read full article on Sky News
            <svg className="ml-2 -mr-1 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </a>
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
