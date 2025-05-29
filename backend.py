from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai
import json
from datetime import datetime

app = Flask(__name__)
CORS(app)

openai.api_key = os.environ.get("OPENAI_API_KEY")

@app.route("/explain", methods=["POST"])
def explain():
    data = request.get_json()
    symptom = data.get("symptom", "")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful health assistant that explains medical symptoms clearly."},
                {"role": "user", "content": f"What could it mean if someone is experiencing: {symptom}?"}
            ]
        )
        explanation = response['choices'][0]['message']['content']

        # Save to logs.json
        log_entry = {
            "symptom": symptom,
            "explanation": explanation,
            "timestamp": datetime.utcnow().isoformat()
        }
        logs = []
        if os.path.exists("logs.json"):
            with open("logs.json", "r") as f:
                logs = json.load(f)
        logs.append(log_entry)
        with open("logs.json", "w") as f:
            json.dump(logs, f)

        return jsonify({"explanation": explanation})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/logs", methods=["GET"])
def get_logs():
    try:
        with open("logs.json", "r") as f:
            logs = json.load(f)
        return jsonify({"logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500