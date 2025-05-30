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

@app.route("/match-specialty", methods=["POST"])
def match_specialty():
    data = request.get_json()
    symptom = data.get("symptom", "")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful health assistant. Given a medical symptom or description, respond with only the type of doctor or medical specialty the patient should see. Keep it very short."},
                {"role": "user", "content": f"What kind of doctor should someone see if they are experiencing: {symptom}?"}
            ]
        )
        specialty = response['choices'][0]['message']['content'].strip()
        return jsonify({"specialty": specialty})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/find-doctors", methods=["POST"])
def find_doctors():
    data = request.get_json()
    specialty = data.get("specialty", "").lower()

    # Sample mock doctor database
    mock_doctors = [
        {"name": "Dr. Emily Zhang", "specialty": "dermatologist", "location": "Downtown Clinic", "phone": "555-123-4567"},
        {"name": "Dr. Raj Patel", "specialty": "cardiologist", "location": "Heart Health Center", "phone": "555-987-6543"},
        {"name": "Dr. Maya Lopez", "specialty": "pediatrician", "location": "Family Care Pediatrics", "phone": "555-222-3344"},
        {"name": "Dr. James Kim", "specialty": "otolaryngologist", "location": "Ear, Nose & Throat Associates", "phone": "555-333-2211"},
        {"name": "Dr. Sarah Green", "specialty": "dentist", "location": "Bright Smile Dental", "phone": "555-456-7890"},
    ]

    matching_doctors = [doc for doc in mock_doctors if specialty in doc["specialty"].lower()]

    return jsonify({"doctors": matching_doctors})