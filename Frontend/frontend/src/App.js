import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './Pages/Home';
import SearchResults from './Pages/SearchResults';
import ArticleDetail from './Pages/ArticleDetail';
import Header from './Components/Header';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50"> {/* Full viewport height with light gray background */}
        <Header />
        <main className="container mx-auto px-4 py-6"> {/* Centered container with padding */}
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search/:entity" element={<SearchResults />} />
            <Route path="/article/:id" element={<ArticleDetail />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;