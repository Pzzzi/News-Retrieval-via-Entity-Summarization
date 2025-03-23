from flask import Flask, request, jsonify
from flask_cors import CORS
from Services.Search.entity_search import entity_search
from Services.Summarization.entity_summarization import get_article_summary

app = Flask(__name__)
CORS(app)

# === API Route for Entity Search ===
@app.route("/search", methods=["GET"])
def search():
    entity = request.args.get("entity")
    if not entity:
        return jsonify({"error": "Entity is required!"}), 400

    results = entity_search(entity)
    return jsonify(results)


# === API Route for Article Summary ===
@app.route('/article_summary/<article_id>', methods=['GET'])
def fetch_article_summary(article_id):
    summary = get_article_summary(article_id)
    return jsonify(summary)


if __name__ == "__main__":
    app.run(debug=True)


