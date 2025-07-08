import time
from flask import Flask, jsonify, send_from_directory
import threading
import os

app = Flask(__name__)

cache = {
    'data': [],
    'timestamp': 0
}

def fetch_and_cache_cloud_data():
    import requests

    points = []
    try:
        with open('points.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                lat_str, lon_str = line.split(',')
                points.append({
                    'lat': float(lat_str),
                    'lon': float(lon_str)
                })
    except Exception as e:
        print(f"Error reading points.txt: {e}")
        return []

    results = []

    for point in points:
        lat = point['lat']
        lon = point['lon']
        try:
            url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=cloud_cover&timezone=Europe/Berlin'
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
            cloud = data.get('current', {}).get('cloud_cover', 0)
            results.append({
                'lat': lat,
                'lon': lon,
                'cloud': cloud if isinstance(cloud, (int, float)) else 0
            })
        except Exception as e:
            print(f"Error fetching cloud for {lat},{lon}: {e}")
            results.append({
                'lat': lat,
                'lon': lon,
                'cloud': 0
            })

    return results

def refresh_cache():
    while True:
        print("Refreshing cloud data cache...")
        data = fetch_and_cache_cloud_data()
        base_lat = 52.48
        base_lon = 13.35
        scale_x = 15
        scale_y = 15
        lon_km = 111 * (abs(base_lat) / 90)
        lat_km = 111

        processed = []
        for p in data:
            x = (p['lon'] - base_lon) * lon_km * scale_x
            y = (p['lat'] - base_lat) * lat_km * scale_y
            processed.append({'x': x, 'y': y, 'cloud': p['cloud']})
        
        cache['data'] = processed
        cache['timestamp'] = time.time()
        print("✅ Cache updated:", cache)
        time.sleep(1800)  # 30분 간격

@app.route('/api/cloud-data')
def cloud_data():
    return jsonify(cache['data'])

@app.route('/fonts/<path:filename>')
def serve_fonts(filename):
    return send_from_directory(os.path.join(app.root_path, 'fonts'), filename)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

threading.Thread(target=refresh_cache, daemon=True).start()

if __name__ == '__main__':
    app.run(debug=True)
