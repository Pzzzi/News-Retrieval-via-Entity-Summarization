import React from 'react';

function ArticleCard({ article, onClick, onEntityClick = () => { } }) {
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

  // Entity type to color mapping
  const getEntityColor = (type) => {
    switch(type) {
      case 'PERSON':
        return { bg: 'bg-blue-100', text: 'text-blue-800', hover: 'hover:bg-blue-200' };
      case 'NORP':
        return { bg: 'bg-purple-100', text: 'text-purple-800', hover: 'hover:bg-purple-200' };
      case 'FAC':
        return { bg: 'bg-amber-100', text: 'text-amber-800', hover: 'hover:bg-amber-200' };
      case 'ORG':
        return { bg: 'bg-rose-100', text: 'text-rose-800', hover: 'hover:bg-rose-200' };
      case 'GPE':
        return { bg: 'bg-green-100', text: 'text-green-800', hover: 'hover:bg-green-200' };
      case 'LOC':
        return { bg: 'bg-emerald-100', text: 'text-emerald-800', hover: 'hover:bg-emerald-200' };
      case 'PRODUCT':
        return { bg: 'bg-cyan-100', text: 'text-cyan-800', hover: 'hover:bg-cyan-200' };
      case 'EVENT':
        return { bg: 'bg-red-100', text: 'text-red-800', hover: 'hover:bg-red-200' };
      case 'WORK_OF_ART':
        return { bg: 'bg-fuchsia-100', text: 'text-fuchsia-800', hover: 'hover:bg-fuchsia-200' };
      case 'LAW':
        return { bg: 'bg-violet-100', text: 'text-violet-800', hover: 'hover:bg-violet-200' };
      case 'LANGUAGE':
        return { bg: 'bg-sky-100', text: 'text-sky-800', hover: 'hover:bg-sky-200' };
      case 'DATE':
        return { bg: 'bg-yellow-100', text: 'text-yellow-800', hover: 'hover:bg-yellow-200' };
      case 'TIME':
        return { bg: 'bg-orange-100', text: 'text-orange-800', hover: 'hover:bg-orange-200' };
      case 'PERCENT':
        return { bg: 'bg-lime-100', text: 'text-lime-800', hover: 'hover:bg-lime-200' };
      case 'MONEY':
        return { bg: 'bg-teal-100', text: 'text-teal-800', hover: 'hover:bg-teal-200' };
      case 'QUANTITY':
        return { bg: 'bg-pink-100', text: 'text-pink-800', hover: 'hover:bg-pink-200' };
      case 'ORDINAL':
        return { bg: 'bg-indigo-100', text: 'text-indigo-800', hover: 'hover:bg-indigo-200' };
      case 'CARDINAL':
        return { bg: 'bg-amber-100', text: 'text-amber-800', hover: 'hover:bg-amber-200' };
      default:
        return { bg: 'bg-gray-100', text: 'text-gray-800', hover: 'hover:bg-gray-200' };
    }
  };

  return (
    <div
      onClick={() => onClick(article._id)}
      className="border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow cursor-pointer h-full flex flex-col bg-white"
    >
      {/* Only render image container if article.image exists */}
      {article.image && (
        <div className="w-full h-48 overflow-hidden">
          <img
            src={article.image}
            alt={article.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
      )}

      <div className="p-4 flex-grow flex flex-col">
        <h3 className="text-lg font-semibold mb-2 text-gray-900">
          {article.title || 'Untitled Article'}
        </h3>

        <div className="flex items-center text-sm text-gray-500 space-x-3 mb-3">
          <span>{parseDate(article.date)}</span>
          <span className="h-1 w-1 bg-gray-400 rounded-full"></span>
          <span>{getDomain(article.url)}</span>
        </div>

        {(article.matched_entities?.length > 0 || article.entities?.length > 0) && (
          <div className="flex flex-wrap gap-2 mt-2 mb-4">
            {(article.matched_entities || article.entities).map((entity, idx) => {
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
                  className={`${colors.bg} ${colors.text} ${colors.hover} px-2 py-0.5 rounded-full text-xs transition-colors`}
                  title={`Type: ${entityType}`}
                >
                  {entity.name || entity.normalized_label || entity.text}
                </button>
              );
            })}
          </div>
        )}

        <a
          href={article.url || '#'}
          className="mt-auto text-blue-600 hover:text-blue-800 text-sm font-medium inline-flex items-center self-start"
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
        >
          Read full article
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 ml-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </a>
      </div>
    </div>
  );
}

export default ArticleCard;
