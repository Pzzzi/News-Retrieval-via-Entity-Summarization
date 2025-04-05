function ArticleList({ articles, onArticleClick }) {
    return (
      <div className="article-list">
        <h4>Articles:</h4>
        <ul>
          {articles.map((article, index) => (
            <li key={index}>
              <button 
                onClick={() => onArticleClick(article._id)}
                className="article-link"
              >
                {article.title}
              </button>
              <div className="article-date">
                {new Date(article.date).toLocaleDateString()}
              </div>
            </li>
          ))}
        </ul>
      </div>
    );
  }
  
  export default ArticleList;