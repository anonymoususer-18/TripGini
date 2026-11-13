
import os
import pymysql
import jwt

from datetime import datetime, timedelta, timezone
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps

# Load environment settings from the main project folder
load_dotenv()

app = Flask(__name__)

# MySQL configuration
# Use Docker's MySQL hostname when running inside Docker.
# Locally, it defaults to 127.0.0.1.
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "tripgenie")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "tripgenie")

JWT_SECRET = os.getenv("JWT_SECRET")

if not MYSQL_PASSWORD:
    raise RuntimeError("MYSQL_PASSWORD is missing from .env")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is missing from .env")


# Connect to MySQL
def get_db():
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )


# Create users table if it does not exist
def create_users_table():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    finally:
        connection.close()


# Create a JWT authentication token
def create_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=1)
    }

    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


# Check authentication token
def token_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        authorization = request.headers.get("Authorization", "")

        if not authorization.startswith("Bearer "):
            return jsonify({"error": "Authentication token required"}), 401

        token = authorization.split(" ", 1)[1]

        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"]
            )
            request.user_id = payload["user_id"]

        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid or expired token"}), 401

        return function(*args, **kwargs)

    return wrapper


# Health check
@app.route("/health", methods=["GET"])
def health():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return jsonify({
            "status": "healthy",
            "service": "user-service",
            "database": "connected"
        })
    finally:
        connection.close()


# Register a new user
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must contain at least 8 characters"}), 400

    password_hash = generate_password_hash(password)

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (name, email, password_hash)
                VALUES (%s, %s, %s)
                """,
                (name, email, password_hash)
            )

            user_id = cursor.lastrowid

        return jsonify({
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "name": name,
                "email": email
            }
        }), 201

    except pymysql.err.IntegrityError:
        return jsonify({"error": "Email already registered"}), 409

    finally:
        connection.close()


# Login an existing user
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users WHERE email = %s",
                (email,)
            )
            user = cursor.fetchone()

        if not user or not check_password_hash(
            user["password_hash"], password
        ):
            return jsonify({"error": "Invalid email or password"}), 401

        token = create_token(user["id"])

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        })

    finally:
        connection.close()


# Get logged-in user's profile
@app.route("/me", methods=["GET"])
@token_required
def get_profile():
    connection = get_db()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, name, email, created_at FROM users WHERE id = %s",
                (request.user_id,)
            )
            user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        user["created_at"] = user["created_at"].isoformat()

        return jsonify({"user": user})

    finally:
        connection.close()


if __name__ == "__main__":
    create_users_table()
    print("User Service database table is ready.")
    app.run(host="0.0.0.0", port=5001, debug=True)
