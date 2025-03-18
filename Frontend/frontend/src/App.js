import React, { useState } from "react";
import axios from "axios";
import EntityGraph from "./EntityGraph";

function App() {
  const [query, setQuery] = useState("");
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const searchEntity = async (entity = query) => {
    setLoading(true);
    try {
      const response = await axios.get(`http://127.0.0.1:5000/search?entity=${entity}`);
      setData(response.data);
      setQuery(entity);  // Update query with new entity
    } catch (error) {
      console.error("Error fetching data:", error);
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
          <EntityGraph
            entity={data.entity}
            relatedEntities={data.related_entities}
            onEntityClick={searchEntity}
          />
          <h4>Articles:</h4>
          <ul>
            {data.articles.map((article, index) => (
              <li key={index}>
                <a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;

