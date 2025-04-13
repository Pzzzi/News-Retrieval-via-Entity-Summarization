import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="bg-white shadow-sm sticky top-0 z-10">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link 
          to="/" 
          className="text-xl font-bold text-blue-600 hover:text-blue-800 transition-colors flex items-center"
        >
          <span className="mr-2">🔍</span>
          Entity-Based News Search
        </Link>
        
        <nav className="flex space-x-6">
          <Link 
            to="/" 
            className="text-gray-700 hover:text-blue-600 transition-colors font-medium"
          >
            Home
          </Link>
          {/* Add more nav links as needed */}
        </nav>
      </div>
    </header>
  );
}

export default Header;