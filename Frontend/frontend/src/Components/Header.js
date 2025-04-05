import { Link } from 'react-router-dom';

function Header() {
  return (
    <header className="app-header">
      <Link to="/" className="logo">
        Entity-Based News Search
      </Link>
      <nav>
        <Link to="/">Home</Link>
      </nav>
    </header>
  );
}

export default Header;