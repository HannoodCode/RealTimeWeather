from flask import Flask, render_template, jsonify
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import folium
from folium import plugins

app = Flask(__name__)

# Separate UAE cities
UAE_CITIES = {
    "Dubai": [25.2048, 55.2708],
    "Abu Dhabi": [24.4539, 54.3773],
    "Sharjah": [25.3573, 55.4033],
    "Ajman": [25.4052, 55.5136],
    "Ras Al Khaimah": [25.7895, 55.9432],
    "Fujairah": [25.1288, 56.3265],
    "Umm Al Quwain": [25.5647, 55.5532]
}

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
    try:
        # Get the latest data for each city
        latest_data = df.groupby('city').first().reset_index()
        
        # Create a map centered on UAE with limited scrolling
        weather_map = folium.Map(
            location=[24.4539, 54.3773],  # Centered on Abu Dhabi
            zoom_start=4,
            tiles='CartoDB positron',  # English map tiles
            prefer_canvas=True,
            min_zoom=2,
            max_bounds=True,
            min_lat=-90,
            max_lat=90,
            min_lon=-180,
            max_lon=180,
            max_bounds_viscosity=1.0,
            control_scale=True
        )
        
        # First add UAE cities
        uae_heat_data = []
        for _, row in latest_data.iterrows():
            city = row['city']
            if city in UAE_CITIES:
                lat, lon = UAE_CITIES[city]
                add_city_marker(weather_map, city, lat, lon, row)
                uae_heat_data.append([lat, lon, row['temperature']])
        
        # Add UAE heat map first if we have data
        if uae_heat_data:
            plugins.HeatMap(
                uae_heat_data,
                radius=25,
                blur=15,
                max_zoom=1,
                min_opacity=0.5
            ).add_to(weather_map)
        
        # Then add other cities
        other_heat_data = []
        for _, row in latest_data.iterrows():
            city = row['city']
            if city in CITY_COORDINATES and city not in UAE_CITIES:
                lat, lon = CITY_COORDINATES[city]
                add_city_marker(weather_map, city, lat, lon, row)
                other_heat_data.append([lat, lon, row['temperature']])
        
        # Add global heat map if we have data
        if other_heat_data:
            plugins.HeatMap(
                other_heat_data,
                radius=25,
                blur=15,
                max_zoom=1,
                min_opacity=0.5
            ).add_to(weather_map)

        # Add fullscreen option only
        plugins.Fullscreen().add_to(weather_map)
        
        # Add custom JavaScript to limit scrolling
        custom_js = """
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            var map = document.querySelector('#map');
            if (map) {
                map._leaflet.setMaxBounds([[-90,-180], [90,180]]);
                map._leaflet.setMinZoom(2);
            }
        });
        </script>
        """
        weather_map.get_root().html.add_child(folium.Element(custom_js))
        
        return weather_map._repr_html_()
        
    except Exception as e:
        print(f"Error creating map: {e}")
        return None

def add_city_marker(map_obj, city, lat, lon, row):
    """Add a city marker to the map"""
    # Create info window content
    popup_html = f"""
        <div class="weather-popup" style="
            background-color: white;
            padding: 12px;
            border-radius: 8px;
            border: 2px solid {get_temperature_color(row['temperature'])};
            font-family: Arial;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            min-width: 200px;
            z-index: 1000;
        ">
            <div style="
                font-weight: bold;
                font-size: 18px;
                margin-bottom: 8px;
                color: {get_temperature_color(row['temperature'])};
                border-bottom: 2px solid {get_temperature_color(row['temperature'])}20;
                padding-bottom: 5px;
            ">
                {city}
            </div>
            <div style="display: grid; grid-gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🌡️</span>
                    <span><strong>Temperature:</strong> {row['temperature']}°C</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">💧</span>
                    <span><strong>Humidity:</strong> {row['humidity']}%</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">💨</span>
                    <span><strong>Wind Speed:</strong> {row['wind_speed']} km/h</span>
                </div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px;">🌤️</span>
                    <span><strong>Condition:</strong> {row['condition']}</span>
                </div>
            </div>
        </div>
    """
    
    # Create a unique ID for the marker
    marker_id = f"marker_{city.replace(' ', '_').replace(',', '').replace('.', '')}"
    
    # Add marker with popup
    marker = folium.CircleMarker(
        location=[lat, lon],
        radius=8,
        popup=folium.Popup(
            popup_html,
            max_width=300,
            show=False,
            sticky=False
        ),
        color=get_temperature_color(row['temperature']),
        fill=True,
        fill_color=get_temperature_color(row['temperature']),
        fill_opacity=0.7,
        weight=2,
        opacity=1
    )
    
    # Add the marker to the map
    marker.add_to(map_obj)
    
    # Add click event handler using Element
    click_script = f"""
        <script>
            (function() {{
                var marker = document.querySelector('#{marker_id}');
                if (marker) {{
                    marker.addEventListener('click', function(e) {{
                        // Close all popups
                        var popups = document.querySelectorAll('.leaflet-popup');
                        popups.forEach(function(popup) {{
                            popup.remove();
                        }});
                        
                        // Show this marker's popup
                        var popup = L.popup()
                            .setLatLng([{lat}, {lon}])
                            .setContent(`{popup_html}`)
                            .openOn(map);
                            
                        // Close popup when clicking elsewhere on the map
                        map.once('click', function() {{
                            map.closePopup(popup);
                        }});
                    }});
                }}
            }})();
        </script>
    """
    
    map_obj.get_root().html.add_child(folium.Element(click_script))

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
    try:
        df = get_weather_data()
        if df.empty:
            raise ValueError("No weather data available")
            
        weather_map_html = create_weather_map(df)
        latest_data = df.groupby('city').first().reset_index()
        
        # Prioritize UAE cities in the weather cards
        uae_data = latest_data[latest_data['city'].isin(UAE_CITIES.keys())]
        other_data = latest_data[~latest_data['city'].isin(UAE_CITIES.keys())]
        sorted_data = pd.concat([uae_data, other_data])
        
        return render_template('index.html', 
                             weather_map=weather_map_html,
                             latest_data=sorted_data.to_dict('records'))
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html', 
                             weather_map=None,
                             latest_data=[])

if __name__ == '__main__':
    app.run(debug=True, port=5000) 