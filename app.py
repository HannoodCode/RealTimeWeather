from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import folium
from folium import plugins

app = Flask(__name__)

# Dictionary of city coordinates
CITY_COORDINATES = {
    "Kabul": [34.5253, 69.1783],
    "Tirana": [41.3275, 19.8187],
    "Algiers": [36.7538, 3.0588],
    "Andorra la Vella": [42.5063, 1.5218],
    "Luanda": [-8.8383, 13.2344],
    "Buenos Aires": [-34.6037, -58.3816],
    "Yerevan": [40.1792, 44.4991],
    "Canberra": [-35.2809, 149.1300],
    "Vienna": [48.2082, 16.3738],
    "Baku": [40.4093, 49.8671],
    "Nassau": [25.0343, -77.3963],
    "Manama": [26.2285, 50.5860],
    "Dhaka": [23.8103, 90.4125],
    "Bridgetown": [13.1132, -59.5988],
    "Minsk": [53.9045, 27.5615],
    "Brussels": [50.8503, 4.3517],
    "Belmopan": [17.2514, -88.7705],
    "Porto-Novo": [6.4969, 2.6283],
    "Thimphu": [27.4716, 89.6386],
    "La Paz": [-16.4897, -68.1193],
    "Sarajevo": [43.8564, 18.4131],
    "Gaborone": [-24.6282, 25.9231],
    "Brasília": [-15.7975, -47.8919],
    "Sofia": [42.6977, 23.3219],
    "Ouagadougou": [12.3714, -1.5197],
    "Gitega": [-3.4271, 29.9251],
    "Phnom Penh": [11.5564, 104.9282],
    "Yaoundé": [3.8480, 11.5021],
    "Ottawa": [45.4215, -75.6972],
    "Beijing": [39.9042, 116.4074],
    "Bogotá": [4.7110, -74.0721],
    "Copenhagen": [55.6761, 12.5683],
    "Cairo": [30.0444, 31.2357],
    "London": [51.5074, -0.1278],
    "Paris": [48.8566, 2.3522],
    "Berlin": [52.5200, 13.4050],
    "Athens": [37.9838, 23.7275],
    "New Delhi": [28.6139, 77.2090],
    "Jakarta": [-6.2088, 106.8456],
    "Tehran": [35.6892, 51.3890],
    "Baghdad": [33.3152, 44.3661],
    "Dublin": [53.3498, -6.2603],
    "Jerusalem": [31.7683, 35.2137],
    "Rome": [41.9028, 12.4964],
    "Tokyo": [35.6762, 139.6503],
    "Amman": [31.9454, 35.9284],
    "Nairobi": [-1.2921, 36.8219],
    "Kuwait City": [29.3759, 47.9774],
    "Kuala Lumpur": [3.1390, 101.6869],
    "Mexico City": [19.4326, -99.1332],
    "Rabat": [34.0209, -6.8416],
    "Amsterdam": [52.3676, 4.9041],
    "Wellington": [-41.2866, 174.7756],
    "Oslo": [59.9139, 10.7522],
    "Muscat": [23.5880, 58.3829],
    "Islamabad": [33.6844, 73.0479],
    "Manila": [14.5995, 120.9842],
    "Warsaw": [52.2297, 21.0122],
    "Lisbon": [38.7223, -9.1393],
    "Doha": [25.2854, 51.5310],
    "Moscow": [55.7558, 37.6173],
    "Riyadh": [24.7136, 46.6753],
    "Singapore": [1.3521, 103.8198],
    "Madrid": [40.4168, -3.7038],
    "Stockholm": [59.3293, 18.0686],
    "Bern": [46.9480, 7.4474],
    "Damascus": [33.5138, 36.2765],
    "Bangkok": [13.7563, 100.5018],
    "Abu Dhabi": [24.4539, 54.3773],
    "Dubai": [25.2048, 55.2708],
    "London": [51.5074, -0.1278],
    "Washington, D.C.": [38.9072, -77.0369],
    "Montevideo": [-34.9011, -56.1645],
    "Tashkent": [41.2995, 69.2401],
    "Vatican City": [41.9029, 12.4534],
    "Hanoi": [21.0285, 105.8542]
}

def get_weather_data():
    """Fetch weather data from SQLite database"""
    conn = sqlite3.connect('weather_data.db')
    query = """
    SELECT city, temperature, humidity, wind_speed, condition, timestamp
    FROM weather_data
    WHERE timestamp >= datetime('now', '-1 day')
    ORDER BY timestamp DESC
    """
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    conn.close()
    return df

def create_weather_map(df):
    """Create a Folium map with weather data"""
    # Get the latest data for each city
    latest_data = df.groupby('city').first().reset_index()
    
    # Create a map centered on Dubai
    weather_map = folium.Map(
        location=[25.2048, 55.2708],
        zoom_start=3,
        tiles='cartodbpositron'
    )
    
    # Add weather data markers for each city
    for _, row in latest_data.iterrows():
        city = row['city']
        if city in CITY_COORDINATES:
            lat, lon = CITY_COORDINATES[city]
            
            # Create tooltip with HTML styling
            tooltip_html = f"""
                <div style="
                    background-color: white;
                    padding: 8px;
                    border-radius: 4px;
                    border: 2px solid {get_temperature_color(row['temperature'])};
                    font-family: Arial;
                    font-size: 14px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                ">
                    <strong>{city}</strong><br>
                    🌡️ {row['temperature']}°C
                </div>
            """
            
            # Create popup content with more detailed information
            popup_content = f"""
                <div style='font-family: Arial; width: 200px; padding: 10px;'>
                    <h4 style='margin:0 0 10px 0; color: #2C3E50;'>{city}</h4>
                    <div style='background: {get_temperature_color(row['temperature'])}20; padding: 10px; border-radius: 5px;'>
                        <p style='margin:5px 0'><b>🌡️ Temperature:</b> {row['temperature']}°C</p>
                        <p style='margin:5px 0'><b>💧 Humidity:</b> {row['humidity']}%</p>
                        <p style='margin:5px 0'><b>💨 Wind Speed:</b> {row['wind_speed']} km/h</p>
                        <p style='margin:5px 0'><b>🌤️ Condition:</b> {row['condition']}</p>
                    </div>
                </div>
            """
            
            # Add marker with custom icon, tooltip, and popup
            folium.CircleMarker(
                location=[lat, lon],
                radius=8,
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=folium.Tooltip(
                    tooltip_html,
                    permanent=False,
                    sticky=True
                ),
                color=get_temperature_color(row['temperature']),
                fill=True,
                fill_color=get_temperature_color(row['temperature']),
                fill_opacity=0.7,
                weight=2
            ).add_to(weather_map)
    
    # Add a temperature heatmap layer with reduced radius
    heat_data = [
        [CITY_COORDINATES[row['city']][0], 
         CITY_COORDINATES[row['city']][1], 
         row['temperature']] 
        for _, row in latest_data.iterrows() 
        if row['city'] in CITY_COORDINATES
    ]
    plugins.HeatMap(
        heat_data,
        radius=25,
        blur=15,
        max_zoom=1
    ).add_to(weather_map)
    
    return weather_map._repr_html_()

def get_temperature_color(temp):
    """Return color based on temperature"""
    if temp < 0:
        return 'blue'
    elif temp < 10:
        return 'lightblue'
    elif temp < 20:
        return 'green'
    elif temp < 30:
        return 'orange'
    else:
        return 'red'

@app.route('/')
def index():
    df = get_weather_data()
    weather_map_html = create_weather_map(df)
    latest_data = df.groupby('city').first().reset_index()
    return render_template('index.html', 
                         weather_map=weather_map_html,
                         latest_data=latest_data.to_dict('records'))

if __name__ == '__main__':
    app.run(debug=True, port=5000) 