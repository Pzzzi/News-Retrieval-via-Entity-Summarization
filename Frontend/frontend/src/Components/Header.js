import { Link, useLocation } from 'react-router-dom';
import SearchBar from './SearchBar';

function Header() {
  const location = useLocation();

  return (
    <header className="bg-white shadow-sm sticky top-0 z-20">
      <div className="container mx-auto px-4 py-4 flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        {/* Logo */}
        <div className="flex items-center justify-between">
          <Link 
            to="/" 
            className="text-xl font-bold text-blue-600 hover:text-blue-800 transition-colors flex items-center"
          >
            <span className="mr-2">🔍</span>
            Entity-Based News Search
          </Link>
        </div>

        {/* Search Bar (only show on routes where it makes sense) */}
        {location.pathname !== '/article' && (
          <div className="absolute left-1/2 transform -translate-x-1/2 w-full max-w-xl">
            <SearchBar />
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
