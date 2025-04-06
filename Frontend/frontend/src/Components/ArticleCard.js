import React from 'react';
import '../styles/ArticleCard.css';

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
    <div className="article-card" onClick={() => onClick(article._id)}>
      {article.image && (
        <div className="article-image-container">
          <img 
            src={article.image} 
            alt={article.title} 
            className="article-image"
            onError={(e) => {
              e.target.style.display = 'none'; // Hide if image fails to load
            }}
          />
        </div>
      )}
      <div className="article-card-content">
        <h3 className="article-title">{article.title || 'Untitled Article'}</h3>
        <div className="article-meta">
          <span className="article-date">{parseDate(article.date)}</span>
          <span className="article-source">{getDomain(article.url)}</span>
        </div>
        <a 
          href={article.url || '#'} 
          className="article-link" 
          target="_blank" 
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
        >
          Read full article →
        </a>
      </div>
    </div>
  );
};

export default ArticleCard;