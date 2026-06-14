from flask import Flask, request, render_template, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
import os
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

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/weather')
@limiter.limit("10 per minute")  # Limit this route to 10 requests per minute
def weather():
    latitude = request.args.get('latitude', '0')  # Default to '0' if not provided
    print(latitude)
    longitude = request.args.get('longitude', '0')  # Default to '0' if not provided
    print(longitude)
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{latitude},{longitude}?key={api_key}"
    try:
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
            # Pass the data dict to your HTML template
            return render_template('weather.html', weather=weather_data)
        elif response.status_code == 429:
            return render_template('weather.html', error="Rate limit exceeded. Please try again later.")
        else:
            return render_template('weather.html', error="Could not retrieve weather data.")
    except Exception as e:
        return render_template('weather.html', error="Connection error occurred.")

if __name__ == '__main__':
    app.run(debug=True)  