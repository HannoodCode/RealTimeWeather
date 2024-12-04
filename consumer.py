#!/usr/bin/env python
import json
from confluent_kafka import Consumer
from datetime import datetime
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
KAFKA_USERNAME = os.getenv('KAFKA_USERNAME')
KAFKA_PASSWORD = os.getenv('KAFKA_PASSWORD')

def setup_database():
    """Create SQLite database and table for weather data"""
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS weather_data
                 (city TEXT, temperature REAL, humidity REAL, 
                  wind_speed REAL, condition TEXT, timestamp TEXT)''')
    conn.commit()
    return conn

def store_weather_data(conn, data):
    """Store weather data in SQLite database"""
    try:
        print(f"Received data length: {len(data)}")
        print(f"Received data type: {type(data)}")
        print(f"Raw received data: {data}")  # Print complete raw data
        
        # Only try to parse if we have data
        if not data:
            print("Empty data received")
            return
            
        weather = json.loads(data)
        c = conn.cursor()
        
        # Debug print
        print(f"Successfully parsed JSON data")
        print(f"Parsed data - City: {weather['location']['name']}, "
              f"Temp: {weather['current']['temp_c']}, "
              f"Humidity: {weather['current']['humidity']}")
        
        c.execute('''INSERT INTO weather_data VALUES (?, ?, ?, ?, ?, ?)''',
                 (weather['location']['name'],
                  weather['current']['temp_c'],
                  weather['current']['humidity'],
                  weather['current']['wind_kph'],
                  weather['current']['condition']['text'],
                  weather['timestamp']))
        conn.commit()
        print("Successfully stored in database")
        
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Raw data: {repr(data)}")
    except Exception as e:
        print(f"Error storing data: {e}")
        print(f"Raw data: {repr(data)}")

if __name__ == '__main__':
    # Kafka configuration
    config = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'sasl.username': KAFKA_USERNAME,
        'sasl.password': KAFKA_PASSWORD,
        'security.protocol': 'SASL_SSL',
        'sasl.mechanisms': 'PLAIN',
        'group.id': 'weather-monitoring-group',
        'auto.offset.reset': 'earliest'
    }

    # Create Consumer instance
    consumer = Consumer(config)
    
    # Setup database
    db_conn = setup_database()

    # Subscribe to topic
    topic = "weather"
    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                print(f"Consumer error: {msg.error()}")
                continue

            try:
                # Get the value and decode it
                value = msg.value()
                if value is None:
                    print("Received null message value")
                    continue
                    
                decoded_value = value.decode('utf-8')
                store_weather_data(db_conn, decoded_value)
                
            except Exception as e:
                print(f"Error processing message: {e}")
                print(f"Raw message value: {repr(msg.value())}")
            
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()
        db_conn.close()