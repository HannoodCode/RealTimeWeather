#!/usr/bin/env python
import json
import time
import requests
from datetime import datetime
from confluent_kafka import Producer
import os
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

# Separate UAE cities from other capitals
UAE_CITIES = {
    "Dubai": [25.2048, 55.2708],
    "Abu Dhabi": [24.4539, 54.3773],
    "Sharjah": [25.3573, 55.4033],
    "Ajman": [25.4052, 55.5136],
    "Ras Al Khaimah": [25.7895, 55.9432],
    "Fujairah": [25.1288, 56.3265],
    "Umm Al Quwain": [25.5647, 55.5532]
}

# Rest of the world capitals
WORLD_CAPITALS = {
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

def fetch_weather_data(api_key, city):
    """Fetch weather data from WeatherAPI.com"""
    base_url = "http://api.weatherapi.com/v1/current.json"
    
    # Handle special cases for city names
    api_city = city
    if city == "Washington, D.C.":
        api_city = "Washington DC"  # WeatherAPI prefers this format
    
    params = {
        'key': api_key,
        'q': api_city,
        'aqi': 'yes'
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        # Ensure we use our original city name in the data
        if city == "Washington, D.C.":
            data['location']['name'] = "Washington, D.C."
        print(f"Successfully fetched data for {city}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather data for {city}: {e}")
        return None

def fetch_initial_cities(producer, api_key, topic):
    """Fetch UAE cities first for quick initial load"""
    print("\nFetching UAE cities first...")
    
    def fetch_and_produce(city):
        weather_data = fetch_weather_data(api_key, city)
        if weather_data:
            try:
                weather_data['timestamp'] = datetime.now().isoformat()
                json_data = json.dumps(weather_data)
                producer.produce(
                    topic=topic,
                    key=city.encode('utf-8'),
                    value=json_data.encode('utf-8'),
                    callback=delivery_callback
                )
            except Exception as e:
                print(f"Error processing data for {city}: {e}")
        return city

    # Use ThreadPoolExecutor to fetch UAE cities in parallel
    with ThreadPoolExecutor(max_workers=len(UAE_CITIES)) as executor:
        futures = [executor.submit(fetch_and_produce, city) for city in UAE_CITIES.keys()]
        for future in as_completed(futures):
            try:
                city = future.result()
                print(f"Completed fetching {city}")
            except Exception as e:
                print(f"Error in parallel fetch: {e}")

    producer.poll(0)
    producer.flush()

def fetch_remaining_cities(producer, api_key, topic):
    """Fetch remaining world capitals in the background"""
    print("\nFetching remaining world capitals...")
    for city in WORLD_CAPITALS.keys():
        weather_data = fetch_weather_data(api_key, city)
        if weather_data:
            try:
                weather_data['timestamp'] = datetime.now().isoformat()
                json_data = json.dumps(weather_data)
                producer.produce(
                    topic=topic,
                    key=city.encode('utf-8'),
                    value=json_data.encode('utf-8'),
                    callback=delivery_callback
                )
                time.sleep(1)  # Longer delay for remaining cities
            except Exception as e:
                print(f"Error processing data for {city}: {e}")
        producer.poll(0)
    producer.flush()

def delivery_callback(err, msg):
    """Delivery callback for Kafka producer"""
    if err:
        print(f'ERROR: Message failed delivery: {err}')
    else:
        print(f"Produced weather data for {msg.key().decode('utf-8')}")

if __name__ == '__main__':
    # Kafka configuration
    config = {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS'),
        'sasl.username': os.getenv('KAFKA_USERNAME'),
        'sasl.password': os.getenv('KAFKA_PASSWORD'),
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'acks': 'all'
    }

    # WeatherAPI configuration
    weather_api_key = os.getenv("WEATHERAPI_KEY")
    cities = list(WORLD_CAPITALS.keys())
    topic = "weather"

    # Create Producer instance
    producer = Producer(config)

    try:
        while True:
            # First fetch UAE cities quickly
            fetch_initial_cities(producer, weather_api_key, topic)
            
            # Then fetch remaining cities in the background
            fetch_remaining_cities(producer, weather_api_key, topic)
            
            print("\nWaiting 6 hours before next update...")
            time.sleep(21600)  # Wait 6 hours before next round
            
    except KeyboardInterrupt:
        print("Stopping producer...")
    finally:
        producer.flush()