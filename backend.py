from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/explain", methods=["POST"])
def explain():
    data = request.get_json()
    symptom = data.get("symptom", "")
    return jsonify({
        "explanation": f"Fake explanation for: {symptom}"
    })