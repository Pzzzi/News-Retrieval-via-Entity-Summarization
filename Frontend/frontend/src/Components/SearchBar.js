import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const SearchBar = ({ onSearchSelect }) => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length < 2) {
        setSuggestions([]);
        return;
      }

      try {
        const res = await axios.get(`http://127.0.0.1:5000/suggest?q=${query}`);
        setSuggestions(res.data.results);
      } catch (err) {
        console.error('Error fetching suggestions:', err);
      }
    };

    const delayDebounce = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(delayDebounce);
  }, [query]);

  const handleSelect = (text) => {
    const encodedEntity = encodeURIComponent(text);
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
    
    // Navigate to search results page
    navigate(`/search/${encodedEntity}`);
    
    // Optional: Call parent component's handler if provided
    if (onSearchSelect) {
      onSearchSelect(text);
    }
  };

  return (
    <div className="relative w-full max-w-xl mx-auto">
      <input
        className="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm 
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  text-gray-700 placeholder-gray-400 transition-all"
        type="text"
        placeholder="Search for entities..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
      />

      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-10 w-full mt-1 bg-white border border-gray-200 
                      rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {suggestions.map((s, index) => (
            <li 
              key={index} 
              className="px-4 py-2 hover:bg-gray-100 cursor-pointer transition-colors
                        flex items-center border-b border-gray-100 last:border-b-0"
              onClick={() => handleSelect(s.text)}
              onMouseDown={(e) => e.preventDefault()} 
            >
              <span className={`px-2 py-1 text-xs rounded-full mr-2
                ${s.type === 'PERSON' ? 'bg-blue-100 text-blue-800' : 
                  s.type === 'ORG' ? 'bg-green-100 text-green-800' :
                  'bg-purple-100 text-purple-800'}`}>
                {s.type}
              </span>
              <span className="truncate">{s.text}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default SearchBar;
