import React, { useState } from "react";
import axios from "axios";
import EntityGraph from "../Components/EntityGraph";

function App() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedSummary, setSelectedSummary] = useState(null);

  const searchEntity = async (entity = query) => {
    setLoading(true);
    try {
      const response = await axios.get(`http://127.0.0.1:5000/search?entity=${entity}`);
      setData(response.data);
      setQuery(entity);
      setSelectedSummary(null);
    } catch (error) {
      console.error("Error fetching data:", error);
    }
    setLoading(false);
  };

  const fetchSummary = async (articleId) => {
    setLoading(true);
    try {
      const response = await axios.get(`http://127.0.0.1:5000/article_summary/${articleId}`);
      setSelectedSummary(response.data.summary);
    } catch (error) {
      console.error("Error fetching summary:", error);
      setSelectedSummary("No summary available.");
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h2>🔍 Entity-Based News Search</h2>
      <input
        type="text"
        placeholder="Search for an entity (e.g., Tesla)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{ padding: "10px", width: "300px" }}
      />
      <button onClick={() => searchEntity()} style={{ padding: "10px", marginLeft: "10px" }}>Search</button>

      {loading && <p>Loading...</p>}

      {data && (
        <div>
          <h3>Results for: <strong>{data.entity.id}</strong></h3>
          
          {/* Updated EntityGraph with links prop */}
          <EntityGraph
            entity={data.entity}
            relatedEntities={data.related_entities}
            links={data.links} 
            onEntityClick={searchEntity}
          />
          
          <div style={{ display: "flex", marginTop: "20px" }}>
            <div style={{ flex: 1 }}>
              <h4>Articles:</h4>
              <ul style={{ listStyle: "none", padding: 0 }}>
                {data.articles.map((article, index) => (
                  <li key={index} style={{ marginBottom: "8px" }}>
                    <button 
                      onClick={() => fetchSummary(article._id)} 
                      style={{ 
                        background: "none", 
                        border: "none", 
                        color: "blue", 
                        cursor: "pointer", 
                        textDecoration: "underline", 
                        padding: 0,
                        textAlign: "left"
                      }}
                    >
                      {article.title}
                    </button>
                    <div style={{ fontSize: "0.8em", color: "#666" }}>
                      {new Date(article.date).toLocaleDateString()}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            
            {selectedSummary && (
              <div style={{ flex: 1, paddingLeft: "20px" }}>
                <h4>Summary:</h4>
                <div style={{ 
                  background: "#f5f5f5", 
                  padding: "15px", 
                  borderRadius: "5px",
                  whiteSpace: "pre-wrap"
                }}>
                  {selectedSummary}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;