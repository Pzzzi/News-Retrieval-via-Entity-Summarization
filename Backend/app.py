from flask import Flask, request, jsonify
from flask_cors import CORS
from Services.Search.entity_search import entity_search
from Services.Summarization.entity_summarization import get_article_summary
from Services.Summarization.entity_summarization import get_entity_summary
from Services.Home.home_data import get_homepage_data
from Services.Search.search_bar import suggest_entities

app = Flask(__name__)
CORS(app)

@app.route("/search", methods=["GET"])
def search():
    entity = request.args.get("entity")
    if not entity:
        return jsonify({"error": "Entity is required!"}), 400
    results = entity_search(entity)
    return jsonify(results)

# Summary-only endpoint
@app.route('/article_summary/<article_id>', methods=['GET'])
def fetch_article_summary(article_id):
    summary_data = get_article_summary(article_id)
    if "error" in summary_data:
        return jsonify(summary_data), 404 if summary_data["error"] == "Article not found" else 500
    return jsonify(summary_data)

# Homepage data endpoint
@app.route('/api/home-data', methods=['GET'])
def home_data():
    try:
        data = get_homepage_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Search bar suggestion
@app.route('/suggest')
def suggest():
    query = request.args.get('q', '')
    suggestions = suggest_entities(query)
    return jsonify(suggestions)  # This will properly format the response

@app.route('/entity_summary_titles/<entity_name>', methods=['GET'])
def fetch_entity_summary_titles(entity_name):
    summary_data = get_entity_summary(entity_name)
    if "error" in summary_data:
        return jsonify(summary_data), 404
    return jsonify(summary_data)

if __name__ == "__main__":
    app.run(debug=True)