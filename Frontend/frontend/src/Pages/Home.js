import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import SearchBar from '../Components/SearchBar';

function Home() {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (entity) => {
    navigate(`/search/${entity}`);
  };

  return (
    <div className="home-page">
      <h2>🔍 Entity-Based News Search</h2>
      <SearchBar 
        query={query}
        setQuery={setQuery}
        onSearch={handleSearch}
      />
      <div className="recent-searches">
        <h3>Try searching for:</h3>
        <button onClick={() => handleSearch('UK')}>UK</button>
        <button onClick={() => handleSearch('Tesla')}>Tesla</button>
        <button onClick={() => handleSearch('Apple')}>Apple</button>
      </div>
    </div>
  );
}

export default Home;