import time
import random
import urllib.request
import json

BATCH_ID = "VAX-HARDWARE-001"
BACKEND_URL = "http://127.0.0.1:5000/reading"

def send_reading(temp, humidity, anomaly):
    data = json.dumps({
        "batch_id": BATCH_ID,
        "temperature": temp,
        "humidity": humidity,
        "anomaly": anomaly
    }).encode('utf-8')
    
    req = urllib.request.Request(BACKEND_URL, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        return f"Error: {e}"

def run_hardware():
    print(f"Starting hardware simulation for {BATCH_ID}...")
    while True:
        temp = round(random.uniform(4.0, 8.0), 2)
        humidity = round(random.uniform(45.0, 55.0), 2)
        anomaly = False if 5.0 <= temp <= 7.0 else True
        
        print(f"Reading -> Temp: {temp}°C, Humidity: {humidity}% | Anomaly: {anomaly}")
        res = send_reading(temp, humidity, anomaly)
        print(f"Backend response: {res}")
        
        time.sleep(2)

if __name__ == "__main__":
    run_hardware()
