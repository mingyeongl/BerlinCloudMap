import os
import threading
import time
from flask import Flask, jsonify, send_from_directory, render_template
import csv
import requests

app = Flask(__name__, static_folder="static", template_folder="templates")

CLOUD_DATA_URL = "https://your-cloud-url/points.txt"  # 필요시 수정
CACHE = {"data": [], "timestamp": 0}
CACHE_TTL = 60  # 초

def fetch_and_cache_cloud_data():
    try:
        response = requests.get(CLOUD_DATA_URL)
        response.raise_for_status()
        content = response.text.strip().splitlines()
        reader = csv.reader(content, delimiter=',')
        data = [{"x": float(x), "y": float(y), "z": float(z)} for x, y, z in reader]
        CACHE["data"] = data
        CACHE["timestamp"] = time.time()
        print("✅ Cache updated:", CACHE)
    except Exception as e:
        print("⚠️ Error fetching cloud data:", e)

@app.route("/api/points")
def get_points():
    if time.time() - CACHE["timestamp"] > CACHE_TTL:
        fetch_and_cache_cloud_data()
    return jsonify(CACHE["data"])

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/fonts/<path:filename>")
def serve_fonts(filename):
    return send_from_directory(os.path.join(app.static_folder, "fonts"), filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    fetch_and_cache_cloud_data()
    app.run(host="0.0.0.0", port=port)
