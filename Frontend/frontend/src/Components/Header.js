import { Link, useLocation } from 'react-router-dom';
import SearchBar from './SearchBar';

function Header() {
  const location = useLocation();

  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-6 py-4">
        <div className="relative flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 group">
            <span className="text-3xl font-extrabold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent tracking-tight transition-all duration-300 group-hover:scale-105 group-hover:tracking-wide">
              Entity
              <span className="text-blue-500 font-semibold">News</span>
            </span>
          </Link>

          {/* Search Bar - Centered */}
          {location.pathname !== '/article' && (
            <div className="absolute left-1/2 -translate-x-1/2 w-full max-w-xl px-4">
              <SearchBar />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;

