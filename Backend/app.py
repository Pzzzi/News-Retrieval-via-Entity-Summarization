from flask import Flask, request, jsonify
from flask_cors import CORS
from Services.Search.entity_search import entity_search

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


if __name__ == "__main__":
    app.run(debug=True)

