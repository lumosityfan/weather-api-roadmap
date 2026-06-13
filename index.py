from flask import Flask, render_template, jsonify
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
@limiter.limit("10 per minute")  # Limit this route to 10 requests per minute
def index():
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/London,UK?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Extract specific data points
            weather_data = {
                "resolvedAddress": data["resolvedAddress"],
                "description": data["description"],
                "currentConditions": data["currentConditions"],
                "days": data["days"][:7]  # Get the first 7 days of forecast
            }
            # Pass the data dict to your HTML template
            return render_template('index.html', weather=weather_data)
        elif response.status_code == 429:
            return render_template('index.html', error="Rate limit exceeded. Please try again later.")
        else:
            return render_template('index.html', error="Could not retrieve weather data.")
    except Exception as e:
        return render_template('index.html', error="Connection error occurred.")

if __name__ == '__main__':
    app.run(debug=True)  