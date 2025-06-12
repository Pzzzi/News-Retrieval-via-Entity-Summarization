import React from 'react';

function ArticleCard({ article = {}, onClick, onEntityClick = () => { } }) {
  // Keep all your existing utility functions exactly the same
  const getDomain = (url) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace('www.', '');
    } catch (e) {
      return url || 'Source not available';
    }
  };

  const parseDate = (dateStr) => {
    if (!dateStr) return 'Unknown date';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
  };

  // Entity type to color mapping - enhanced with gradients and modern colors
  const getEntityColor = (type) => {
    switch(type) {
      case 'PERSON':
        return { bg: 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200', text: 'text-blue-700', hover: 'hover:from-blue-100 hover:to-indigo-100 hover:border-blue-300' };
      case 'NORP':
        return { bg: 'bg-gradient-to-r from-purple-50 to-violet-50 border-purple-200', text: 'text-purple-700', hover: 'hover:from-purple-100 hover:to-violet-100 hover:border-purple-300' };
      case 'FAC':
        return { bg: 'bg-gradient-to-r from-amber-50 to-orange-50 border-amber-200', text: 'text-amber-700', hover: 'hover:from-amber-100 hover:to-orange-100 hover:border-amber-300' };
      case 'ORG':
        return { bg: 'bg-gradient-to-r from-rose-50 to-pink-50 border-rose-200', text: 'text-rose-700', hover: 'hover:from-rose-100 hover:to-pink-100 hover:border-rose-300' };
      case 'GPE':
        return { bg: 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-200', text: 'text-green-700', hover: 'hover:from-green-100 hover:to-emerald-100 hover:border-green-300' };
      case 'LOC':
        return { bg: 'bg-gradient-to-r from-emerald-50 to-teal-50 border-emerald-200', text: 'text-emerald-700', hover: 'hover:from-emerald-100 hover:to-teal-100 hover:border-emerald-300' };
      case 'PRODUCT':
        return { bg: 'bg-gradient-to-r from-cyan-50 to-sky-50 border-cyan-200', text: 'text-cyan-700', hover: 'hover:from-cyan-100 hover:to-sky-100 hover:border-cyan-300' };
      case 'EVENT':
        return { bg: 'bg-gradient-to-r from-red-50 to-rose-50 border-red-200', text: 'text-red-700', hover: 'hover:from-red-100 hover:to-rose-100 hover:border-red-300' };
      case 'WORK_OF_ART':
        return { bg: 'bg-gradient-to-r from-fuchsia-50 to-purple-50 border-fuchsia-200', text: 'text-fuchsia-700', hover: 'hover:from-fuchsia-100 hover:to-purple-100 hover:border-fuchsia-300' };
      case 'LAW':
        return { bg: 'bg-gradient-to-r from-violet-50 to-indigo-50 border-violet-200', text: 'text-violet-700', hover: 'hover:from-violet-100 hover:to-indigo-100 hover:border-violet-300' };
      case 'LANGUAGE':
        return { bg: 'bg-gradient-to-r from-sky-50 to-blue-50 border-sky-200', text: 'text-sky-700', hover: 'hover:from-sky-100 hover:to-blue-100 hover:border-sky-300' };
      case 'DATE':
        return { bg: 'bg-gradient-to-r from-yellow-50 to-amber-50 border-yellow-200', text: 'text-yellow-700', hover: 'hover:from-yellow-100 hover:to-amber-100 hover:border-yellow-300' };
      case 'TIME':
        return { bg: 'bg-gradient-to-r from-orange-50 to-red-50 border-orange-200', text: 'text-orange-700', hover: 'hover:from-orange-100 hover:to-red-100 hover:border-orange-300' };
      case 'PERCENT':
        return { bg: 'bg-gradient-to-r from-lime-50 to-green-50 border-lime-200', text: 'text-lime-700', hover: 'hover:from-lime-100 hover:to-green-100 hover:border-lime-300' };
      case 'MONEY':
        return { bg: 'bg-gradient-to-r from-teal-50 to-cyan-50 border-teal-200', text: 'text-teal-700', hover: 'hover:from-teal-100 hover:to-cyan-100 hover:border-teal-300' };
      case 'QUANTITY':
        return { bg: 'bg-gradient-to-r from-pink-50 to-rose-50 border-pink-200', text: 'text-pink-700', hover: 'hover:from-pink-100 hover:to-rose-100 hover:border-pink-300' };
      case 'ORDINAL':
        return { bg: 'bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200', text: 'text-indigo-700', hover: 'hover:from-indigo-100 hover:to-purple-100 hover:border-indigo-300' };
      case 'CARDINAL':
        return { bg: 'bg-gradient-to-r from-amber-50 to-yellow-50 border-amber-200', text: 'text-amber-700', hover: 'hover:from-amber-100 hover:to-yellow-100 hover:border-amber-300' };
      default:
        return { bg: 'bg-gradient-to-r from-gray-50 to-slate-50 border-gray-200', text: 'text-gray-700', hover: 'hover:from-gray-100 hover:to-slate-100 hover:border-gray-300' };
    }
  };

  // Keep image handling logic exactly the same
  const placeholderImage = 'https://cdn.pixabay.com/photo/2014/08/07/21/13/newspaper-412809_1280.jpg';
  const [imageSrc, setImageSrc] = React.useState(article?.image || placeholderImage);
  const [imageError, setImageError] = React.useState(false);

  const handleImageError = () => {
    if (!imageError) {
      setImageSrc(placeholderImage);
      setImageError(true);
    }
  };

  return (
    <div
      onClick={() => onClick(article._id)}
      className="relative border border-gray-200/60 rounded-2xl overflow-hidden shadow-sm hover:shadow-2xl hover:shadow-gray-900/10 transition-all duration-500 cursor-pointer h-full flex flex-col bg-white group backdrop-blur-sm hover:-translate-y-1 hover:border-gray-300/60"
    >
      {/* Subtle gradient overlay for depth */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/80 via-transparent to-gray-50/40 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      {/* Image container with enhanced effects */}
      <div className="relative w-full h-48 overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100">
        {!imageError ? (
          <img
            src={imageSrc}
            alt={article?.title || 'Article image'}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-700 ease-out"
            onError={handleImageError}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 via-gray-50 to-white">
            <div className="relative">
              <div className="w-16 h-16 bg-gradient-to-br from-gray-300 to-gray-400 rounded-2xl flex items-center justify-center shadow-lg">
                <svg 
                  className="w-8 h-8 text-white" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="absolute -top-1 -right-1 w-3 h-3 bg-gradient-to-br from-blue-400 to-blue-500 rounded-full animate-pulse" />
            </div>
          </div>
        )}
        
        {/* Subtle overlay for better text contrast */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/5 via-transparent to-transparent" />
      </div>

      {/* Content container with enhanced spacing */}
      <div className="relative p-6 flex-grow flex flex-col">
        {/* Title with enhanced typography */}
        <h3 className="text-xl font-bold mb-3 text-gray-900 group-hover:text-gray-700 transition-colors line-clamp-2 leading-tight tracking-tight">
          {article?.title || 'Untitled Article'}
        </h3>

        {/* Meta information with enhanced styling */}
        <div className="flex items-center text-sm text-gray-500 space-x-3 mb-4">
          <div className="flex items-center space-x-1">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="font-medium text-gray-600">{parseDate(article?.date)}</span>
          </div>
          <div className="h-4 w-px bg-gray-300" />
          <div className="flex items-center space-x-1">
            <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
            </svg>
            <span className="text-gray-600 font-medium">{getDomain(article?.url)}</span>
          </div>
        </div>

        {/* Entities with premium styling */}
        {(article?.matched_entities?.length > 0 || article?.entities?.length > 0) && (
          <div className="flex flex-wrap gap-2 mb-6">
            {(article?.matched_entities || article?.entities)?.map((entity, idx) => {
              const entityType = Array.isArray(entity.type) ? entity.type[0] : entity.type;
              const colors = getEntityColor(entityType);
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onEntityClick(entity);
                  }}
                  className={`${colors.bg} ${colors.text} ${colors.hover} px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-300 border transform hover:scale-105 hover:shadow-md backdrop-blur-sm`}
                  title={`Type: ${entityType}`}
                >
                  {entity.name || entity.normalized_label || entity.text}
                </button>
              );
            })}
          </div>
        )}

        {/* Read link with premium styling */}
        <div className="mt-auto">
          <a
            href={article?.url || '#'}
            className="group/link inline-flex items-center px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-sm font-semibold rounded-xl transition-all duration-300 transform hover:scale-105 hover:shadow-lg hover:shadow-blue-500/25"
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            <span>Read full article</span>
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              className="h-4 w-4 ml-2 group-hover/link:translate-x-1 transition-transform duration-300" 
              fill="none" 
              viewBox="0 0 24 24" 
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
            
            {/* Subtle shine effect */}
            <div className="absolute inset-0 -top-px rounded-xl bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover/link:opacity-100 group-hover/link:animate-shimmer" />
          </a>
        </div>
      </div>
    </div>
  );
}

export default ArticleCard;