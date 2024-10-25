import gradio as gr
import requests
from datetime import datetime, timedelta
import pandas as pd
import altair as alt

# Function to get coordinates from city name using Nominatim
def get_coordinates(city_name):
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {
        "User-Agent": "WeatherDashboardApp/1.0 (contact@example.com)"  # Replace with your app name and contact info
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        location_data = response.json()
        if location_data:
            location = location_data[0]
            return float(location['lat']), float(location['lon'])
        else:
            return None, None
    else:
        return None, None

# Function to get weather data from Open-Meteo
def get_weather_data(lat, lon, hours):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m&forecast_days=2"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# Function to get and visualize weather data
def weather_dashboard(city_name, forecast_duration, parameter_options):
    lat, lon = get_coordinates(city_name)
    if lat is None or lon is None:
        return "City not found. Please check the spelling or try adding the country name (e.g., 'San Francisco, USA').", None
    
    data = get_weather_data(lat, lon, forecast_duration)
    if data is None:
        return "Failed to retrieve data.", None

    # Current Weather Summary
    temperature = f"{data['hourly']['temperature_2m'][0]}°C"
    humidity = f"{data['hourly']['relative_humidity_2m'][0]}%"
    wind_speed = f"{data['hourly']['wind_speed_10m'][0]} m/s"
    summary = (
        f"<div style='text-align: center; margin-bottom: 20px;'>"
        f"<h2>Current Weather Summary</h2>"
        f"<div style='display: flex; justify-content: space-around; align-items: center;'>"
        f"<div style='text-align: center;'><h3>🌡️ Temperature</h3><p style='font-size: 20px; font-weight: bold;'>{temperature}</p></div>"
        f"<div style='text-align: center;'><h3>💧 Humidity</h3><p style='font-size: 20px; font-weight: bold;'>{humidity}</p></div>"
        f"<div style='text-align: center;'><h3>🌬️ Wind Speed</h3><p style='font-size: 20px; font-weight: bold;'>{wind_speed}</p></div>"
        f"</div>"
        f"</div>"
    )

    # Prepare time and parameter data
    times = [datetime.now() + timedelta(hours=i) for i in range(forecast_duration)]
    df = pd.DataFrame({"Time": times})

    # Create data for selected parameters
    charts = []
    for parameter in parameter_options:
        if parameter == "Temperature (°C)":
            df["Temperature (°C)"] = data['hourly']['temperature_2m'][:forecast_duration]
            chart = alt.Chart(df).mark_line(color='#FF5733', strokeWidth=2).encode(
                x=alt.X('Time:T', title='Time', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Temperature (°C):Q', title='Temperature (°C)', scale=alt.Scale(domain=[df["Temperature (°C)"].min() - 2, df["Temperature (°C)"].max() + 2])),
                tooltip=['Time', 'Temperature (°C)']
            ).properties(
                title='Hourly Temperature Forecast',
                width=400,
                height=250
            )
            charts.append(chart)
        elif parameter == "Humidity (%)":
            df["Humidity (%)"] = data['hourly']['relative_humidity_2m'][:forecast_duration]
            chart = alt.Chart(df).mark_line(color='#33CFFF', strokeWidth=2).encode(
                x=alt.X('Time:T', title='Time', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Humidity (%):Q', title='Humidity (%)', scale=alt.Scale(domain=[df["Humidity (%)"].min() - 5, 100])),
                tooltip=['Time', 'Humidity (%)']
            ).properties(
                title='Hourly Humidity Forecast',
                width=400,
                height=250
            )
            charts.append(chart)
        elif parameter == "Wind Speed (m/s)":
            df["Wind Speed (m/s)"] = data['hourly']['wind_speed_10m'][:forecast_duration]
            chart = alt.Chart(df).mark_line(color='#82E0AA', strokeWidth=2).encode(
                x=alt.X('Time:T', title='Time', axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Wind Speed (m/s):Q', title='Wind Speed (m/s)', scale=alt.Scale(domain=[0, df["Wind Speed (m/s)"].max() + 2])),
                tooltip=['Time', 'Wind Speed (m/s)']
            ).properties(
                title='Hourly Wind Speed Forecast',
                width=400,
                height=250
            )
            charts.append(chart)

    if charts:
        chart_output = alt.vconcat(*charts).configure_title(
            fontSize=18,
            anchor='start'
        ).configure_concat(
            spacing=20
        ).configure_axis(
            labelFontSize=12,
            titleFontSize=14
        )
    else:
        chart_output = None

    return summary, chart_output

# Gradio UI
city_input = gr.Textbox(label="Enter City Name", value="San Francisco", placeholder="e.g., San Francisco, USA")
forecast_slider = gr.Slider(label="Select forecast duration (hours)", minimum=12, maximum=48, value=24, step=12)
parameter_checkbox = gr.CheckboxGroup(
    label="Choose weather parameters to display:",
    choices=["Temperature (°C)", "Humidity (%)", "Wind Speed (m/s)"],
    value=["Temperature (°C)", "Humidity (%)"]
)

iface = gr.Interface(
    fn=weather_dashboard,
    inputs=[city_input, forecast_slider, parameter_checkbox],
    outputs=[
        gr.HTML(label="Current Weather Summary"),
        gr.Plot(label="")
    ],
    title="Real-Time Weather Dashboard",
    description="Get real-time weather updates and visualize temperature, humidity, and wind speed trends by city.",
    theme="default",
    allow_flagging="never"
)

iface.launch()
