from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import openai
import json
from datetime import datetime
import requests

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
    specialty = data.get("specialty", "")
    lat = data.get("latitude")
    lon = data.get("longitude")

    if not lat or not lon:
        return jsonify({"error": "Missing latitude or longitude"}), 400

    try:
        # Sample request to the NPI Registry API (replace or extend with a more powerful API if needed)
        response = requests.get(
            "https://npiregistry.cms.hhs.gov/api/",
            params={
                "version": "2.1",
                "limit": 10,
                "taxonomy_description": specialty,
                "postal_code": "",  # Optional if you have it
                "latitude": lat,
                "longitude": lon
            }
        )

        results = response.json().get("results", [])

        doctors = []
        for r in results:
            basic = r.get("basic", {})
            addresses = r.get("addresses", [])
            address = addresses[0] if addresses else {}

            doctors.append({
                "name": f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip(),
                "specialty": specialty,
                "location": address.get("city", "") + ", " + address.get("state", ""),
                "phone": address.get("telephone_number", "N/A")
            })

        return jsonify({"doctors": doctors})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/find-doctors-full", methods=["POST"])
def find_doctors_full():
    data = request.get_json()
    symptom = data.get("symptom", "")
    lat = data.get("latitude")
    lon = data.get("longitude")

    if not symptom or lat is None or lon is None:
        return jsonify({"error": "Missing symptom or location"}), 400

    # Generate explanation
    explanation_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful health assistant that explains medical symptoms clearly."},
            {"role": "user", "content": f"What could it mean if someone is experiencing: {symptom}?"}
        ]
    )
    explanation = explanation_response['choices'][0]['message']['content']

    # Determine specialty
    specialty_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful health assistant. Given a medical symptom or description, respond with only the type of doctor or medical specialty the patient should see. Keep it very short."},
            {"role": "user", "content": f"What kind of doctor should someone see if they are experiencing: {symptom}?"}
        ]
    )
    specialty = specialty_response['choices'][0]['message']['content'].strip()
    # Normalize GPT’s output to a valid NPI taxonomy_description
    mapping = {
        "general practitioner": "General Practice",
        "primary care physician": "Family Practice",
        "family physician": "Family Practice",
        "internist": "Internal Medicine",
        "neurologist": "Neurology",
        "dentist": "Dentistry",
        # …add more as needed…
    }
    lookup_key = specialty.lower()
    taxonomy = mapping.get(lookup_key, specialty)

    # Query doctors
    npireg_response = requests.get(
        "https://npiregistry.cms.hhs.gov/api/",
        params={
            "version": "2.1",
            "limit": 10,
            "taxonomy_description": taxonomy,
            "latitude": lat,
            "longitude": lon
        }
    )
    results = npireg_response.json().get("results", [])
    doctors = []
    for r in results:
        basic = r.get("basic", {})
        addresses = r.get("addresses", [])
        address = addresses[0] if addresses else {}
        doctors.append({
            "name": f"{basic.get('first_name', '')} {basic.get('last_name', '')}".strip(),
            "specialty": taxonomy,
            "location": f"{address.get('city', '')}, {address.get('state', '')}",
            "phone": address.get("telephone_number", "N/A")
        })

    return jsonify({
        "explanation": explanation,
        "specialty": specialty,
        "doctors": doctors
    })