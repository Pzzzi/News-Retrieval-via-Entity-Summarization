import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const SearchBar = ({ onSearchSelect }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [articles, setArticles] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length < 2) {
        setSuggestions([]);
        setArticles([]);
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      try {
        const res = await axios.get(`http://127.0.0.1:5000/suggest?q=${encodeURIComponent(query)}`);
        setSuggestions(res.data.results || []);
        setArticles(res.data.articles || []);
      } catch (err) {
        console.error('Error fetching suggestions:', err);
        setSuggestions([]);
        setArticles([]);
      } finally {
        setIsLoading(false);
      }
    };

    const delayDebounce = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(delayDebounce);
  }, [query]);

  const handleSelect = (entity) => {
    const encodedEntity = encodeURIComponent(entity.label || entity.text);
    setQuery('');
    setSuggestions([]);
    setArticles([]);
    setShowSuggestions(false);
    
    navigate(`/search/${encodedEntity}`);
    
    if (onSearchSelect) {
      onSearchSelect(entity);
    }
  };

  const handleArticleClick = (articleId) => {
    setQuery('');
    setSuggestions([]);
    setArticles([]);
    setShowSuggestions(false);
    navigate(`/article/${articleId}`);
  };

  const hasResults = suggestions.length > 0 || articles.length > 0;
  const showLoading = isLoading && query.length >= 2;

  return (
    <div className="relative w-full max-w-xl mx-auto">
      <div className="relative">
        <input
          className="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm 
                    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                    text-gray-700 placeholder-gray-400 transition-all"
          type="text"
          placeholder="Search for entities or articles..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        />
      </div>

      {showSuggestions && (showLoading || hasResults) && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 
                      rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {/* Loading State */}
          {showLoading && (
            <div className="px-4 py-6 flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}

          {/* Entity Suggestions Section */}
          {!showLoading && suggestions.length > 0 && (
            <>
              <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 text-sm font-medium text-gray-500">
                Entities
              </div>
              <ul>
                {suggestions.map((suggestion, index) => (
                  <li 
                    key={`entity-${suggestion.text}-${index}`} 
                    className="px-4 py-2 hover:bg-gray-100 cursor-pointer transition-colors
                              flex items-center border-b border-gray-100 last:border-b-0"
                    onClick={() => handleSelect(suggestion)}
                    onMouseDown={(e) => e.preventDefault()} 
                  >
                    <span className={`px-2 py-1 text-xs rounded-full mr-2
                      ${suggestion.type === 'PERSON' ? 'bg-blue-100 text-blue-800' : 
                        suggestion.type === 'ORG' ? 'bg-green-100 text-green-800' :
                        'bg-purple-100 text-purple-800'}`}>
                      {suggestion.type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="truncate font-medium">{suggestion.text}</p>
                      {suggestion.text !== suggestion.label && (
                        <p className="truncate text-xs text-gray-500">{suggestion.label}</p>
                      )}
                    </div>
                    {suggestion.count && (
                      <span className="ml-2 px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                        {suggestion.count}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* Article Results Section */}
          {!showLoading && articles.length > 0 && (
            <>
              <div className="px-4 py-2 bg-gray-50 border-b border-gray-200 text-sm font-medium text-gray-500">
                Articles
              </div>
              <ul>
                {articles.map((article, index) => (
                  <li 
                    key={`article-${article._id}-${index}`}
                    className="px-4 py-3 hover:bg-gray-100 cursor-pointer transition-colors
                              border-b border-gray-100 last:border-b-0"
                    onClick={() => handleArticleClick(article._id)}
                    onMouseDown={(e) => e.preventDefault()}
                  >
                    <div className="flex items-start">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{article.title}</p>
                        <div className="flex items-center mt-1 text-xs text-gray-500">
                          <span>{article.source}</span>
                        </div>
                      </div>
                      <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                        Article
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* No Results State */}
          {!showLoading && !hasResults && query.length >= 2 && (
            <div className="px-4 py-3 text-center text-gray-500">
              No results found for "{query}"
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;