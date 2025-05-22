import React from 'react';

function ArticleCard({ article, onClick, onEntityClick = () => {} }) {
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
              // Optional: You could add a fallback here if you want
              // e.target.parentElement.classList.add('bg-gray-100');
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
        
        {article.entities?.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2 mb-4">
            {article.entities.map((entity, idx) => (
              <button
                key={idx}
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onEntityClick(entity);
                }}
                className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full text-xs hover:bg-blue-200"
              >
                {/* Changed from {entity} to {entity.name || entity.normalized_label || entity.text} */}
                {entity.name || entity.normalized_label || entity.text}
              </button>
            ))}
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
