import React from 'react';

const ArticleCard = ({ article, onClick }) => {
  // Parse date from Flask format
  const parseDate = (dateStr) => {
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (e) {
      return dateStr || 'Date not available';
    }
  };

  // Extract domain from URL
  const getDomain = (url) => {
    try {
      const domain = new URL(url).hostname;
      return domain.replace('www.', '');
    } catch (e) {
      return url || 'Source not available';
    }
  };

  return (
    <div 
      className="border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md 
                 transition-shadow cursor-pointer h-full flex flex-col bg-white"
      onClick={() => onClick(article._id)}
    >
      {article.image && (
        <div className="w-full h-48 overflow-hidden">
          <img 
            src={article.image} 
            alt={article.title} 
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none'; // Hide if image fails to load
            }}
          />
        </div>
      )}
      <div className="p-4 flex-grow flex flex-col">
        <h3 className="text-lg font-semibold mb-2 text-gray-900">
          {article.title || 'Untitled Article'}
        </h3>
        
        <div className="flex items-center text-sm text-gray-500 space-x-3 mb-3">
          <span className="article-date">{parseDate(article.date)}</span>
          <span className="h-1 w-1 bg-gray-400 rounded-full"></span>
          <span className="article-source">{getDomain(article.url)}</span>
        </div>
        
        <a 
          href={article.url || '#'} 
          className="mt-auto text-blue-600 hover:text-blue-800 text-sm font-medium
                     inline-flex items-center self-start"
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
};

export default ArticleCard;