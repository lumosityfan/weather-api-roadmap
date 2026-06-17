from flask import Flask, request, render_template, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import redis
import os
import json
from dotenv import load_dotenv

app = Flask(__name__)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Load the environment variables from .env file
load_dotenv()

# Now you can access the environment variable
api_key = os.environ.get('API_KEY')
redis_host = os.environ.get('REDIS_HOST')
redis_port = int(os.environ.get('REDIS_PORT'))
redis_username = os.environ.get('REDIS_USERNAME')
redis_password = os.environ.get('REDIS_PASSWORD')

r = redis.Redis(
    host=redis_host,
    port=redis_port,
    decode_responses=True,
    username=redis_username,
    password=redis_password
)

try:
    r.ping()
    print("Redis connected successfully")
except redis.exceptions.AuthenticationError:
    print("Redis auth failed - check REDIS_PASSWORD")
except redis.exceptions.ConnectionError as e:
    print(f"Redis connection failed: {e}")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/weather')
@limiter.limit("10 per minute")  # Limit this route to 10 requests per minute
def weather():
    latitude = request.args.get('latitude', '0')  # Default to '0' if not provided
    longitude = request.args.get('longitude', '0')  # Default to '0' if not provided
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{latitude},{longitude}?key={api_key}"
    try:
        key = f"{latitude},{longitude}"
        cached_data = r.get(key)
        print(cached_data)
        if cached_data:
            data = json.loads(cached_data)  # Convert string back to dict
            resolvedAddress = data.get("resolvedAddress", "N/A") + " (latitude, longitude)"
            weather_data = {
                "resolvedAddress": resolvedAddress,
                "description": data["description"],
                "currentConditions": data["currentConditions"],
                "days": data["days"][:7]  # Get the first 7 days of forecast
            }
            return render_template('weather.html', weather=weather_data)
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            resolvedAddress = data.get("resolvedAddress", "N/A") + " (latitude, longitude)"
            # Extract specific data points
            print(resolvedAddress)
            weather_data = {
                "resolvedAddress": resolvedAddress,
                "description": data["description"],
                "currentConditions": data["currentConditions"],
                "days": data["days"][:7]  # Get the first 7 days of forecast
            }
            # Store cached data in Redis with an expiration time of 1 hour (3600 seconds)
            r.set(key, json.dumps(data), ex=3600)  # Store the entire response as a string for later retrieval
            # Pass the data dict to your HTML template
            return render_template('weather.html', weather=weather_data)
        elif response.status_code == 429:
            return render_template('weather.html', error="Rate limit exceeded. Please try again later.")
        else:
            return render_template('weather.html', error="Could not retrieve weather data.")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")  # check your terminal/logs
        return render_template('weather.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)  