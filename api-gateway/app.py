
import os
import requests
import jwt

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Flask(__name__)

# Allow the frontend to communicate with the API Gateway
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://127.0.0.1:8080"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

# Docker service names are used when running inside Docker.
# Local addresses remain the default for local development.
USER_SERVICE_URL = os.getenv(
    "USER_SERVICE_URL", "http://127.0.0.1:5001"
)

DESTINATION_SERVICE_URL = os.getenv(
    "DESTINATION_SERVICE_URL", "http://127.0.0.1:5002"
)

AI_SERVICE_URL = os.getenv(
    "AI_SERVICE_URL", "http://127.0.0.1:5003"
)

JWT_SECRET = os.getenv("JWT_SECRET")


# Authentication check
def token_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required"}), 401

        token = auth_header.split(" ", 1)[1]

        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid or expired token"}), 401

        return function(*args, **kwargs)

    return wrapper


# Gateway health
@app.route("/health", methods=["GET"])
def health():
    services = {
        "user": USER_SERVICE_URL + "/health",
        "destination": DESTINATION_SERVICE_URL + "/health",
        "ai": AI_SERVICE_URL + "/health"
    }

    results = {}

    for name, url in services.items():
        try:
            response = requests.get(url, timeout=5)
            results[name] = {
                "status": "healthy" if response.ok else "unhealthy",
                "details": response.json()
            }
        except requests.RequestException:
            results[name] = {"status": "unavailable"}

    overall = all(
        service["status"] == "healthy"
        for service in results.values()
    )

    return jsonify({
        "status": "healthy" if overall else "degraded",
        "services": results
    }), 200 if overall else 503


# User registration
@app.route("/api/register", methods=["POST"])
def register():
    try:
        response = requests.post(
            USER_SERVICE_URL + "/register",
            json=request.get_json(silent=True) or {},
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "User service unavailable"}), 503


# User login
@app.route("/api/login", methods=["POST"])
def login():
    try:
        response = requests.post(
            USER_SERVICE_URL + "/login",
            json=request.get_json(silent=True) or {},
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "User service unavailable"}), 503


# Current user profile
@app.route("/api/me", methods=["GET"])
@token_required
def me():
    try:
        response = requests.get(
            USER_SERVICE_URL + "/me",
            headers={
                "Authorization": request.headers.get("Authorization")
            },
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "User service unavailable"}), 503


# List destinations
@app.route("/api/destinations", methods=["GET"])
def destinations():
    try:
        response = requests.get(
            DESTINATION_SERVICE_URL + "/destinations",
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "Destination service unavailable"}), 503


# Get one destination
@app.route("/api/destinations/<name>", methods=["GET"])
def destination_detail(name):
    try:
        response = requests.get(
            DESTINATION_SERVICE_URL + "/destinations/" + requests.utils.quote(name),
            timeout=10
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "Destination service unavailable"}), 503


# AI travel recommendations
@app.route("/api/recommend", methods=["POST"])
def recommend():
    try:
        response = requests.post(
            AI_SERVICE_URL + "/recommend",
            json=request.get_json(silent=True) or {},
            timeout=55
        )

        return jsonify(response.json()), response.status_code

    except requests.RequestException:
        return jsonify({"error": "AI service unavailable"}), 503


if __name__ == "__main__":
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET is missing from .env")

    print("TripGenie API Gateway starting...")
    app.run(host="0.0.0.0", port=5000, debug=True)
