
import os
from flask import Flask, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv

# Load settings from the main TripGenie .env file
load_dotenv()

app = Flask(__name__)

# MongoDB connection
# Docker uses mongodb as its hostname.
# Local development continues using the URI from .env.
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/tripgenie"
)

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client.get_database()
destinations_collection = db["destinations"]


# 30 sample travel destinations
DESTINATIONS = [
    {
        "name": "Bali",
        "country": "Indonesia",
        "image_url": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=800",
        "budget_level": "medium",
        "best_weather": "warm",
        "vibe_tags": ["beach", "adventure", "culture"],
        "description": "Beautiful beaches, temples and tropical landscapes.",
        "avg_cost_per_day": 55
    },
    {
        "name": "Maldives",
        "country": "Maldives",
        "image_url": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=800",
        "budget_level": "luxury",
        "best_weather": "warm",
        "vibe_tags": ["beach", "relaxation", "adventure"],
        "description": "Luxury island resorts and crystal-clear waters.",
        "avg_cost_per_day": 250
    },
    {
        "name": "Goa",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800",
        "budget_level": "budget",
        "best_weather": "warm",
        "vibe_tags": ["beach", "adventure", "city"],
        "description": "Beaches, nightlife and Portuguese heritage.",
        "avg_cost_per_day": 35
    },
    {
        "name": "Manali",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1626621341517-bbf3d9990a23?w=800",
        "budget_level": "budget",
        "best_weather": "cold",
        "vibe_tags": ["hills", "adventure", "nature"],
        "description": "Snowy mountains, valleys and outdoor adventures.",
        "avg_cost_per_day": 30
    },
    {
        "name": "Paris",
        "country": "France",
        "image_url": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=800",
        "budget_level": "luxury",
        "best_weather": "mild",
        "vibe_tags": ["city", "culture", "romantic"],
        "description": "Art, architecture, cafes and romantic streets.",
        "avg_cost_per_day": 180
    },
    {
        "name": "Tokyo",
        "country": "Japan",
        "image_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=800",
        "budget_level": "medium",
        "best_weather": "mild",
        "vibe_tags": ["city", "culture", "adventure"],
        "description": "Modern technology, ancient temples and amazing food.",
        "avg_cost_per_day": 120
    },
    {
        "name": "Dubai",
        "country": "UAE",
        "image_url": "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=800",
        "budget_level": "luxury",
        "best_weather": "warm",
        "vibe_tags": ["city", "adventure", "shopping"],
        "description": "Skyscrapers, desert safaris and luxury shopping.",
        "avg_cost_per_day": 160
    },
    {
        "name": "Ooty",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1597074866923-dc0589150358?w=800",
        "budget_level": "budget",
        "best_weather": "mild",
        "vibe_tags": ["hills", "nature", "relaxation"],
        "description": "Tea gardens, green hills and peaceful lakes.",
        "avg_cost_per_day": 28
    },
    {
        "name": "Swiss Alps",
        "country": "Switzerland",
        "image_url": "https://images.unsplash.com/photo-1531366936337-7c912a4589a7?w=800",
        "budget_level": "luxury",
        "best_weather": "cold",
        "vibe_tags": ["hills", "adventure", "nature"],
        "description": "Spectacular mountain scenery and skiing.",
        "avg_cost_per_day": 220
    },
    {
        "name": "Phuket",
        "country": "Thailand",
        "image_url": "https://images.unsplash.com/photo-1589394815804-964ed0be2eb5?w=800",
        "budget_level": "medium",
        "best_weather": "warm",
        "vibe_tags": ["beach", "adventure", "relaxation"],
        "description": "Tropical beaches, island hopping and nightlife.",
        "avg_cost_per_day": 65
    },
    {
        "name": "Jaipur",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1599661046827-dacff0c0f09a?w=800",
        "budget_level": "budget",
        "best_weather": "warm",
        "vibe_tags": ["culture", "city", "history"],
        "description": "Royal palaces, forts and colourful markets.",
        "avg_cost_per_day": 30
    },
    {
        "name": "Singapore",
        "country": "Singapore",
        "image_url": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=800",
        "budget_level": "luxury",
        "best_weather": "warm",
        "vibe_tags": ["city", "culture", "adventure"],
        "description": "Modern skyline, gardens and diverse food.",
        "avg_cost_per_day": 150
    },
    {
        "name": "Munnar",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800",
        "budget_level": "budget",
        "best_weather": "mild",
        "vibe_tags": ["hills", "nature", "relaxation"],
        "description": "Rolling tea plantations and misty mountains.",
        "avg_cost_per_day": 32
    },
    {
        "name": "London",
        "country": "United Kingdom",
        "image_url": "https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=800",
        "budget_level": "luxury",
        "best_weather": "cold",
        "vibe_tags": ["city", "culture", "history"],
        "description": "Historic landmarks, museums and city life.",
        "avg_cost_per_day": 190
    },
    {
        "name": "Krabi",
        "country": "Thailand",
        "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800",
        "budget_level": "medium",
        "best_weather": "warm",
        "vibe_tags": ["beach", "adventure", "nature"],
        "description": "Limestone cliffs, beaches and island adventures.",
        "avg_cost_per_day": 60
    },
    {
        "name": "Varkala",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1510414842594-a61c69b5ae57?w=800",
        "budget_level": "budget",
        "best_weather": "warm",
        "vibe_tags": ["beach", "relaxation", "adventure"],
        "description": "Cliffside beaches and peaceful coastal cafes.",
        "avg_cost_per_day": 25
    },
    {
        "name": "New York",
        "country": "USA",
        "image_url": "https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=800",
        "budget_level": "luxury",
        "best_weather": "mild",
        "vibe_tags": ["city", "culture", "adventure"],
        "description": "Famous skyline, entertainment and diverse culture.",
        "avg_cost_per_day": 230
    },
    {
        "name": "Kathmandu",
        "country": "Nepal",
        "image_url": "https://images.unsplash.com/photo-1544735716-392fe2489ffa?w=800",
        "budget_level": "budget",
        "best_weather": "mild",
        "vibe_tags": ["hills", "culture", "adventure"],
        "description": "Himalayan views, temples and mountain culture.",
        "avg_cost_per_day": 35
    },
    {
        "name": "Santorini",
        "country": "Greece",
        "image_url": "https://images.unsplash.com/photo-1533105079780-92b9be482077?w=800",
        "budget_level": "luxury",
        "best_weather": "warm",
        "vibe_tags": ["beach", "culture", "romantic"],
        "description": "Whitewashed villages and beautiful sea views.",
        "avg_cost_per_day": 200
    },
    {
        "name": "Coorg",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1511497584788-876760111969?w=800",
        "budget_level": "budget",
        "best_weather": "mild",
        "vibe_tags": ["hills", "nature", "adventure"],
        "description": "Coffee estates, forests and waterfalls.",
        "avg_cost_per_day": 30
    },
    {
        "name": "Rome",
        "country": "Italy",
        "image_url": "https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=800",
        "budget_level": "medium",
        "best_weather": "mild",
        "vibe_tags": ["culture", "city", "history"],
        "description": "Ancient ruins, Italian food and architecture.",
        "avg_cost_per_day": 140
    },
    {
        "name": "Istanbul",
        "country": "Turkey",
        "image_url": "https://images.unsplash.com/photo-1524231757912-21f4fe3a7200?w=800",
        "budget_level": "medium",
        "best_weather": "mild",
        "vibe_tags": ["culture", "city", "history"],
        "description": "Historic mosques, markets and Bosphorus views.",
        "avg_cost_per_day": 75
    },
    {
        "name": "Alleppey",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800",
        "budget_level": "budget",
        "best_weather": "warm",
        "vibe_tags": ["nature", "relaxation", "culture"],
        "description": "Backwaters, houseboats and peaceful villages.",
        "avg_cost_per_day": 35
    },
    {
        "name": "Queenstown",
        "country": "New Zealand",
        "image_url": "https://images.unsplash.com/photo-1507699622108-4be3abd695ad?w=800",
        "budget_level": "luxury",
        "best_weather": "cold",
        "vibe_tags": ["hills", "adventure", "nature"],
        "description": "Mountain lakes and thrilling outdoor activities.",
        "avg_cost_per_day": 180
    },
    {
        "name": "Cairo",
        "country": "Egypt",
        "image_url": "https://images.unsplash.com/photo-1539768942893-daf53e448371?w=800",
        "budget_level": "budget",
        "best_weather": "warm",
        "vibe_tags": ["culture", "history", "adventure"],
        "description": "Pyramids, ancient history and Egyptian markets.",
        "avg_cost_per_day": 45
    },
    {
        "name": "Amritsar",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1588096344356-5e1d6b5e6c8b?w=800",
        "budget_level": "budget",
        "best_weather": "mild",
        "vibe_tags": ["culture", "history", "city"],
        "description": "Golden Temple and rich Punjabi heritage.",
        "avg_cost_per_day": 25
    },
    {
        "name": "Barcelona",
        "country": "Spain",
        "image_url": "https://images.unsplash.com/photo-1583422409516-2895a77efded?w=800",
        "budget_level": "medium",
        "best_weather": "warm",
        "vibe_tags": ["beach", "city", "culture"],
        "description": "Architecture, Mediterranean beaches and food.",
        "avg_cost_per_day": 130
    },
    {
        "name": "Rishikesh",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1571679654681-ba01b9e1e117?w=800",
        "budget_level": "budget",
        "best_weather": "mild",
        "vibe_tags": ["adventure", "hills", "nature"],
        "description": "River rafting, yoga and Himalayan foothills.",
        "avg_cost_per_day": 28
    },
    {
        "name": "Seychelles",
        "country": "Seychelles",
        "image_url": "https://images.unsplash.com/photo-1514282401047-d79a71a590e8?w=800",
        "budget_level": "luxury",
        "best_weather": "warm",
        "vibe_tags": ["beach", "nature", "relaxation"],
        "description": "Beautiful tropical islands and pristine beaches.",
        "avg_cost_per_day": 210
    },
    {
        "name": "Hampi",
        "country": "India",
        "image_url": "https://images.unsplash.com/photo-1600100397608-f010f2e6f7a2?w=800",
        "budget_level": "budget",
        "best_weather": "warm",
        "vibe_tags": ["culture", "history", "adventure"],
        "description": "Ancient ruins and dramatic rocky landscapes.",
        "avg_cost_per_day": 25
    }
]


# Insert destinations only when the collection is empty
def seed_destinations():
    if destinations_collection.count_documents({}) == 0:
        destinations_collection.insert_many(DESTINATIONS)
        print("Successfully seeded 30 destinations into MongoDB.")
    else:
        print("Destinations already exist. Skipping seed.")


# Health check
@app.route("/health", methods=["GET"])
def health():
    try:
        client.admin.command("ping")
        return jsonify({
            "status": "healthy",
            "service": "destination-service",
            "database": "connected"
        }), 200
    except Exception as error:
        return jsonify({
            "status": "unhealthy",
            "error": str(error)
        }), 503


# Get all destinations
@app.route("/destinations", methods=["GET"])
def get_destinations():
    try:
        destinations = list(
            destinations_collection.find({}, {"_id": 0})
        )

        return jsonify({
            "count": len(destinations),
            "destinations": destinations
        }), 200

    except Exception as error:
        return jsonify({
            "error": "Could not fetch destinations",
            "details": str(error)
        }), 500


# Get one destination by name
@app.route("/destinations/<name>", methods=["GET"])
def get_destination(name):
    destination = destinations_collection.find_one(
        {"name": {"$regex": f"^{name}$", "$options": "i"}},
        {"_id": 0}
    )

    if not destination:
        return jsonify({"error": "Destination not found"}), 404

    return jsonify(destination), 200


# Start the Flask application
if __name__ == "__main__":
    try:
        client.admin.command("ping")
        seed_destinations()
        print("Destination Service is starting on port 5002...")
        app.run(host="0.0.0.0", port=5002, debug=True)
    except Exception as error:
        print("Could not connect to MongoDB:", error)
        raise
