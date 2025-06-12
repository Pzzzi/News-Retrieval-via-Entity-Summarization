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
    if (onSearchSelect) onSearchSelect(entity);
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
      {/* Input */}
      <div className="relative">
        <input
          className="w-full px-5 py-3 rounded-xl border border-gray-300 shadow-md 
                     placeholder-gray-400 text-gray-800 text-sm transition-all
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          type="text"
          placeholder="Search for entities or articles..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        />
      </div>

      {/* Suggestion Dropdown */}
      {showSuggestions && (showLoading || hasResults) && (
        <div className="absolute z-50 w-full mt-2 bg-white border border-gray-200 
                        rounded-xl shadow-lg max-h-96 overflow-y-auto text-sm">
          {/* Loading Spinner */}
          {showLoading && (
            <div className="px-4 py-6 flex justify-center">
              <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full"></div>
            </div>
          )}

          {/* Entity Suggestions */}
          {!showLoading && suggestions.length > 0 && (
            <>
              <div className="px-4 py-2 bg-gray-50 border-b text-gray-500 font-semibold uppercase tracking-wide text-xs">
                Entities
              </div>
              <ul>
                {suggestions.map((suggestion, index) => (
                  <li
                    key={`entity-${suggestion.text}-${index}`}
                    className="flex items-center gap-2 px-4 py-3 cursor-pointer 
                               hover:bg-gray-50 border-b last:border-b-0 transition"
                    onClick={() => handleSelect(suggestion)}
                    onMouseDown={(e) => e.preventDefault()}
                  >
                    <span className={`px-2 py-1 text-[11px] rounded-full 
                      ${suggestion.type === 'PERSON' ? 'bg-blue-100 text-blue-700' :
                        suggestion.type === 'ORG' ? 'bg-green-100 text-green-700' :
                        'bg-purple-100 text-purple-700'}`}>
                      {suggestion.type}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{suggestion.text}</p>
                      {suggestion.text !== suggestion.label && (
                        <p className="text-xs text-gray-500 truncate">{suggestion.label}</p>
                      )}
                    </div>
                    {suggestion.count && (
                      <span className="ml-2 px-2 py-1 text-[11px] bg-gray-100 text-gray-700 rounded-full">
                        {suggestion.count}
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* Article Results */}
          {!showLoading && articles.length > 0 && (
            <>
              <div className="px-4 py-2 bg-gray-50 border-b text-gray-500 font-semibold uppercase tracking-wide text-xs">
                Articles
              </div>
              <ul>
                {articles.map((article, index) => (
                  <li
                    key={`article-${article._id}-${index}`}
                    className="px-4 py-3 hover:bg-gray-50 cursor-pointer 
                               border-b last:border-b-0 transition"
                    onClick={() => handleArticleClick(article._id)}
                    onMouseDown={(e) => e.preventDefault()}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{article.title}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{article.source}</p>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          )}

          {/* No Results */}
          {!showLoading && !hasResults && query.length >= 2 && (
            <div className="px-4 py-4 text-center text-sm text-gray-500">
              No results found for "<span className="font-medium">{query}</span>"
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchBar;
