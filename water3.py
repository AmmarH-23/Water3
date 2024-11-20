from PIL import Image
from datetime import datetime
from streamlit.components.v1 import html
import numpy as np
import matplotlib.pyplot as plt
import folium
from streamlit_folium import folium_static
import secrets
import streamlit as st
import os
import requests
from dotenv import load_dotenv
import openai
import base64

# Load environment variables from .env file
load_dotenv()

# Set up OpenAI API key
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# Set up Google Maps API key
google_maps_api_key = "AIzaSyBwJoBHpsJ5K20tHEF6G5NsVZ0ARbeeSAw"
openweathermap_api_key = "15bde77f4e69ac6a9edddcf25fb3873d"
# Custom CSS for background sidebar
st.markdown("""
    <style>
    .stApp {
        background-color: #87CEEB; /* Light blue background */
    }
    .sidebar .sidebar-content {
        background-color: #4B9CD3; /* Blue sidebar */
        color: white;
    }
    .sidebar .sidebar-content h2 {
        font-size: 1.5em;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Add logo to the sidebar
logo_path = "water logo.png"  # Update with the path to your logo file
st.sidebar.image(logo_path, use_column_width =True)
import base64

def set_background_image(image_path):
    """
    Sets a background image for the Streamlit app.
    :param image_path: Path to the image file or a URL.
    """
    if image_path.startswith("http"):
        # For URLs
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("{image_path}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
    else:
        # For local files
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded_string}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
set_background_image("World Water Day Virtual Background.png")  # Replace with your image path or URL

# App content
st.title("Welcome to Water Habits Chatbot")
st.write("Welcome to Water Habits Chatbot! 💧 This app helps you save water with personalized usage insights, smart irrigation tips, and community reporting tools. Compare your water consumption, get weather-based garden advice, and report local water issues with ease. Together, we can promote sustainable water practices and protect this vital resource!.")

# Sidebar for navigation
st.sidebar.title("Water Habits Chatbot")
selected_topic = st.sidebar.radio("Choose a topic:", 
    ["Personalized Water Usage Insights & Conservation Guidance", 
     "Community Water Conservation Reporting Tool", 
     "Smart Irrigation Recommendations"])

# Function to get average water usage data using OpenAI
def get_average_water_usage(city):
    prompt = (
        f"You are an expert in water conservation. Please provide the average monthly household water usage in gallons specifically for the city of {city}. "
        f"If city-specific data is not available, provide an estimate based on the county-level data. "
        f"If county-level data is also unavailable, provide an estimate for the state of California, ensuring the response is as localized as possible."
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"An error occurred: {e}"
# Function to generate a water usage bar chart
def generate_usage_chart(user_usage, avg_usage, city):
    try:
        if isinstance(avg_usage, str):
            avg_usage_value = float(''.join(filter(str.isdigit, avg_usage)))
        else:
            avg_usage_value = avg_usage
        
        # Data for bar chart
        usage_data = {"Your Usage": user_usage, f"Avg Usage in {city}": avg_usage_value}
        categories = list(usage_data.keys())
        values = list(usage_data.values())

        # Plot bar chart
        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(categories, values, color=['blue', 'green'])

        # Add labels to bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + 5, f'{height:.0f}', ha='center', va='bottom')

        ax.set_title("Water Usage Comparison", fontsize=14)
        ax.set_ylabel("Gallons", fontsize=12)
        ax.set_xlabel("Category", fontsize=12)
        ax.set_ylim(0, max(values) + 10)

        return fig
    except Exception as e:
        st.error(f"Error generating chart: {e}")

#Function to generate water usage insights
def generate_water_usage_insights(user_usage, avg_usage, city, garden_size, plant_types):
    avg_usage_str = avg_usage if isinstance(avg_usage, str) else f"{avg_usage} gallons per month"
    
    prompt = (
        f"You are a water conservation expert. Based on the following information, provide personalized water usage insights and recommendations: \n"
        f"User Monthly Water Usage: {user_usage} gallons\n"
        f"Average Monthly Water Usage for {city}: {avg_usage_str}\n"
        f"Garden Size: {garden_size} square feet\n"
        f"Plant Types: {plant_types}\n"
        f"Please provide a comparison of the user's monthly water usage to the average monthly usage, and suggest ways to reduce usage if it is above average. Ensure that the comparison is based on equivalent units (monthly household usage)."
    )
    try:
        # Use OpenAI API to generate insights
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful water conservation expert."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip() + (f"\n\n(Source for average water usage: Generated by ChatGPT based on available data for {city} or the regional area)")
    except Exception as e:
        return f"An error occurred: {e}"

# Function to display personalized water usage insights
def display_water_usage_insights():
    st.title("Personalized Water Usage Insights & Conservation Guidance")
    city = st.text_input("Enter your city:")
    user_usage = st.number_input("Enter your household water usage for the month (in gallons):", min_value=0, key="usage")
    garden_size = st.number_input("Enter the size of your garden (in square feet):", min_value=1, key="garden_size_insights")
    plant_types = st.text_area("Enter the types of plants in your garden:", key="plant_types")

    if st.button("Get Water Usage Insights & Recommendations"):
        if city:
            avg_usage = get_average_water_usage(city)
            insights = generate_water_usage_insights(user_usage, avg_usage, city, garden_size, plant_types)
            st.write("### Water Usage Insights & Recommendations:")
            st.write(insights)
            st.write("### Visual Comparison:")
            chart = generate_usage_chart(user_usage, avg_usage, city)
            if chart:
                st.pyplot(chart)
        else:
            st.warning("Please enter a valid city name.")
        

# Function to categorize reported issues using OpenAI
def categorize_issue(description):
    prompt = f"You are an assistant that categorizes community-reported water issues. Please categorize the following issue: {description}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"An error occurred: {e}"

# Function to get geocoding data from Google Maps
def get_geocoding_data_google(city):
    url = "https://maps.googleapis.com/maps/api/geocode/json?"
    params = {
        "address": city,
        "key": google_maps_api_key
    }
    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200 and len(data["results"]) > 0:
        location = data["results"][0]["geometry"]["location"]
        return {
            "lat": location["lat"],
            "lon": location["lng"]
        }
    else:
        return f"Error: Unable to fetch geocoding data for {city}. {data.get('error_message', '')}"

# Function to fetch nearby issues
def get_nearby_issues(city):
    """
    Simulates fetching nearby issues. 
    In a real implementation, this would query a database or an API.
    """
    try:
        # Simulated data for demonstration
        issues = [
            {"description": "Leaking fire hydrant", "lat": 37.7749, "lon": -122.4194},
            {"description": "Broken sprinkler system", "lat": 37.7849, "lon": -122.4094},
            {"description": "Water pooling on street", "lat": 37.7649, "lon": -122.4294},
        ]

        # Optionally filter issues by proximity to the city using geocoding
        geocoding_data = get_geocoding_data_google(city)
        if isinstance(geocoding_data, dict):
            user_lat = geocoding_data["lat"]
            user_lon = geocoding_data["lon"]

            # Placeholder: Filter issues if necessary
            # For simplicity, we're returning all issues in this example.
        return issues
    except Exception as e:
        return f"Error fetching issues: {e}"

# Function to display map with nearby issues
def display_nearby_issues_map(city):
    st.write(f"### Nearby Water Issues in {city}")
    issues = get_nearby_issues(city)

    if isinstance(issues, str):  # If error message is returned
        st.warning(issues)
        return

    # Geocoding for city center
    geocoding_data = get_geocoding_data_google(city)
    if isinstance(geocoding_data, str):  # If geocoding error occurs
        st.warning(geocoding_data)
        return

    user_lat = geocoding_data["lat"]
    user_lon = geocoding_data["lon"]

    # Create the map centered on the user's location
    m = folium.Map(location=[user_lat, user_lon], zoom_start=13)

    # Add a marker for the user's location
    folium.Marker([user_lat, user_lon], popup="Your Location", icon=folium.Icon(color="blue")).add_to(m)

    # Add markers for each reported issue
    for issue in issues:
        folium.Marker(
            [issue["lat"], issue["lon"]],
            popup=issue["description"],
            icon=folium.Icon(color="red")
        ).add_to(m)

    # Display the map in Streamlit
    folium_static(m)

# Function to display community conservation reporting tool
def display_conservation_reporting():
    st.title("Community Water Conservation Reporting Tool")
    city = st.text_input("Enter the city where the issue is located:")
    additional_info = st.text_input("Enter additional information to refine location (e.g., cross streets, landmarks):")
    issue_description = st.text_area("Describe the water-related issue (e.g., leaking pipe, visible water wastage, etc.):")
    image = st.file_uploader("Upload a photo of the issue (optional):", type=['jpg', 'jpeg', 'png'])

    if st.button("Report Issue"):
        if city and issue_description:
            location_query = f"{city} {additional_info}" if additional_info else city
            geocoding_data = get_geocoding_data_google(location_query)
            if isinstance(geocoding_data, dict):
                st.write(f"### Location Coordinates for {city}")
                st.write(f"Latitude: {geocoding_data['lat']}, Longitude: {geocoding_data['lon']}")
                category = categorize_issue(issue_description)
                st.write("### Issue Category:")
                st.write(category)
                if image:
                    img = Image.open(image)
                    st.image(img, caption='Uploaded Image', use_column_width=True)
                map_url = f"https://www.google.com/maps/embed/v1/place?key={google_maps_api_key}&q={geocoding_data['lat']},{geocoding_data['lon']}&zoom=12"
                html(f'<iframe width="100%" height="500" frameborder="0" style="border:0" src="{map_url}" allowfullscreen></iframe>', height=500)
                st.success("Thank you for reporting the issue.")
            else:
                st.warning(geocoding_data)
        else:
            st.warning("Please enter both the city and a description of the issue.")

def get_weather_forecast(city):
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {
        "q": city,
        "appid": openweathermap_api_key,
        "units": "imperial"
    }
    response = requests.get(url, params=params)
    data = response.json()

    if response.status_code == 200:
        forecast_list = data["list"]
        daily_forecast = {}
        today = datetime.now().date()

        for forecast in forecast_list:
            forecast_date = datetime.strptime(forecast["dt_txt"], "%Y-%m-%d %H:%M:%S").date()
            if forecast_date <= today or (forecast_date - today).days <= 2:
                if forecast_date not in daily_forecast:
                    daily_forecast[forecast_date] = {
                        "temp_max": forecast["main"]["temp_max"],
                        "temp_min": forecast["main"]["temp_min"],
                        "description": forecast["weather"][0]["description"],
                        "rain_chance": forecast.get("rain", {}).get("3h", 0)
                    }
                else:
                    daily_forecast[forecast_date]["temp_max"] = max(daily_forecast[forecast_date]["temp_max"], forecast["main"]["temp_max"])
                    daily_forecast[forecast_date]["temp_min"] = min(daily_forecast[forecast_date]["temp_min"], forecast["main"]["temp_min"])
                    if "rain" in forecast:
                        daily_forecast[forecast_date]["rain_chance"] += forecast.get("rain", {}).get("3h", 0)
        return daily_forecast
    else:
        return f"Error: Unable to fetch forecast data for {city}. {data.get('message', '')}"

def recommend_irrigation_schedule(weather_data, garden_size, plant_types):
    prompt = (
        f"You are a gardening and irrigation expert. Based on the following weather forecast, provide a detailed smart irrigation recommendation for the user's garden. Assume the user has a smart sprinkler system that can be scheduled to operate at specific times: \n"
        f"Garden Size: {garden_size} square feet\nPlant Types: {plant_types}\n\n"
    )
    for date, forecast in weather_data.items():
        prompt += (
            f"Date: {date}\n"
            f"High Temp: {forecast['temp_max']}°F, Low Temp: {forecast['temp_min']}°F\n"
            f"Weather: {forecast['description']}\n"
            f"Chance of Rain: {forecast['rain_chance']} mm\n\n"
        )
    prompt += (
        "Provide recommendations for how much and when to water the garden based on the forecast. Include specific times for the smart sprinkler system to operate, considering factors such as rain, cloud cover, and temperature. Ensure the output specifies the exact times the sprinklers will be on."
    )
    try:
        # Use OpenAI API to generate irrigation recommendations
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful irrigation expert."},
                {"role": "user", "content": prompt}
            ]
        )
        recommendation = response.choices[0]['message']['content'].strip()
        # Replace phrases to make the recommendation more actionable
        recommendation = recommendation.replace("I suggest running your smart sprinkler system", "The smart sprinkler system will operate").replace("should be on", "will be on")
        return recommendation
    except Exception as e:
        return f"An error occurred: {e}"

# Function to display smart irrigation recommendations
def display_irrigation_recommendations():
    st.title("Smart Irrigation Recommendations")
    city = st.text_input("Enter your city for weather forecast:")
    garden_size = st.number_input("Enter the size of your garden (in square feet):", min_value=1, key="garden_size_irrigation")
    plant_types = st.text_area("Enter the types of plants in your garden:", key="plant_types_irrigation")

    if st.button("Get Irrigation Recommendations"):
        if city:
            weather_data = get_weather_forecast(city)
            if isinstance(weather_data, dict):
                st.write("### Weather Forecast for Today and Next 2 Days:")
                for date, forecast in weather_data.items():
                    st.write(f"**Date: {date}**")
                    st.write(f"High Temp: {forecast['temp_max']}°F, Low Temp: {forecast['temp_min']}°F")
                    st.write(f"Weather: {forecast['description']}")
                    st.write(f"Chance of Rain: {forecast['rain_chance']} mm")
                irrigation_recommendation = recommend_irrigation_schedule(weather_data, garden_size, plant_types)
                st.write("### Irrigation Recommendation:")
                st.write(irrigation_recommendation)
            else:
                st.warning(weather_data)
        else:
            st.warning("Please enter a valid city name.")

# Main show function to display selected topic
def show():
    if selected_topic == "Personalized Water Usage Insights & Conservation Guidance":
        display_water_usage_insights()
    elif selected_topic == "Community Water Conservation Reporting Tool":
        display_conservation_reporting()
        city = st.text_input("Enter your city to find nearby issues:")
        if city:
            display_nearby_issues_map(city)
        else:
            st.warning("Please enter a valid city name.")
        
    elif selected_topic == "Smart Irrigation Recommendations":
        display_irrigation_recommendations()
        



# Run the show function
show()