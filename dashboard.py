import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime, timedelta

def get_weather_data():
    """Fetch weather data from SQLite database"""
    conn = sqlite3.connect('weather_data.db')
    query = """
    SELECT city, temperature, humidity, wind_speed, condition, timestamp
    FROM weather_data
    WHERE timestamp >= datetime('now', '-1 day')
    """
    df = pd.read_sql_query(query, conn)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    conn.close()
    return df

def main():
    st.title("Real-time Weather Dashboard")
    
    # Auto-refresh every minute
    st.set_page_config(page_title="Weather Dashboard", layout="wide")
    
    # Get the latest data
    df = get_weather_data()
    
    # Show current weather for each city
    st.header("Current Weather Conditions")
    latest_data = df.groupby('city').last().reset_index()
    
    # Create columns for each city
    cols = st.columns(len(latest_data))
    for idx, row in latest_data.iterrows():
        with cols[idx]:
            st.subheader(row['city'])
            st.metric("Temperature (°C)", f"{row['temperature']:.1f}")
            st.metric("Humidity (%)", f"{row['humidity']:.0f}")
            st.metric("Wind Speed (km/h)", f"{row['wind_speed']:.1f}")
            st.text(f"Condition: {row['condition']}")
    
    # Temperature trends
    st.header("Temperature Trends")
    fig_temp = px.line(df, x='timestamp', y='temperature', color='city',
                       title="Temperature Variation Over Time")
    st.plotly_chart(fig_temp, use_container_width=True)
    
    # Humidity trends
    st.header("Humidity Trends")
    fig_humidity = px.line(df, x='timestamp', y='humidity', color='city',
                          title="Humidity Variation Over Time")
    st.plotly_chart(fig_humidity, use_container_width=True)
    
    # Wind speed trends
    st.header("Wind Speed Trends")
    fig_wind = px.line(df, x='timestamp', y='wind_speed', color='city',
                       title="Wind Speed Variation Over Time")
    st.plotly_chart(fig_wind, use_container_width=True)

if __name__ == "__main__":
    main() 