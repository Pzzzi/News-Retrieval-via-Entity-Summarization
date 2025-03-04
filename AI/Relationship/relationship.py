import networkx as nx
import matplotlib.pyplot as plt
from pymongo import MongoClient
from collections import defaultdict
import itertools

# Connect to MongoDB
MONGO_URI = "mongodb+srv://Jason:jason1234@cluster0.e3lxn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["news_db"]
collection = db["articles"]

# Initialize graph
G = nx.Graph()

# Dictionary to store entity co-occurrence counts
entity_pairs = defaultdict(int)
entity_frequency = defaultdict(int)

# Process each article (LIMIT to avoid memory overload)
LIMIT = 500  # Adjust based on dataset size
for article in collection.find().limit(LIMIT):  
    entities = [ent["text"] for ent in article.get("entities", [])]

    # Keep only top 5 most frequent entities per article
    entity_counts = {e: entities.count(e) for e in set(entities)}
    top_entities = sorted(entity_counts, key=entity_counts.get, reverse=True)[:5]

    # Track global entity frequency
    for ent in top_entities:
        entity_frequency[ent] += 1

    # Create relationships between top entities
    for entity1, entity2 in itertools.combinations(top_entities, 2):
        entity_pairs[(entity1, entity2)] += 1

# Keep only globally important entities (appearing in at least 3 different articles)
important_entities = {e for e, count in entity_frequency.items() if count >= 3}

# Filter edges: Keep only if both entities are important & co-occur at least 5 times
filtered_edges = {
    (e1, e2): count
    for (e1, e2), count in entity_pairs.items()
    if e1 in important_entities and e2 in important_entities and count >= 5
}

# Add nodes and edges to the graph
for (entity1, entity2), weight in filtered_edges.items():
    G.add_edge(entity1, entity2, weight=weight)

# Keep only top 100 most connected nodes (for readability)
if len(G.nodes) > 100:
    degree_sorted = sorted(G.degree, key=lambda x: x[1], reverse=True)[:100]
    top_nodes = {n for n, _ in degree_sorted}
    G = G.subgraph(top_nodes)

# Plot the graph
plt.figure(figsize=(15, 10))
pos = nx.kamada_kawai_layout(G)  # More optimized for large graphs

# Draw nodes and edges with size & weight scaling
nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=700)
nx.draw_networkx_edges(G, pos, alpha=0.5, width=[G[u][v]["weight"] * 0.2 for u, v in G.edges()], edge_color="gray")
nx.draw_networkx_labels(G, pos, font_size=8)

plt.title("Optimized Entity Relationship Graph")
plt.show()

