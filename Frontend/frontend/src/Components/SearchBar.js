function SearchBar({ query, setQuery, onSearch }) {
    return (
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search for an entity (e.g., Tesla)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && onSearch(query)}
        />
        <button onClick={() => onSearch(query)}>Search</button>
      </div>
    );
  }
  
  export default SearchBar;