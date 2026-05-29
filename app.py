from flask import Flask, jsonify, render_template, request
import random
import datetime
import sqlite3
import os

app = Flask(__name__)

DB_PATH = "crowd_logs.db"

# ─── DATABASE SETUP ───────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS crowd_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            device_count INTEGER NOT NULL,
            crowd_level TEXT NOT NULL,
            wait_time TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# ─── PREDICTION ENGINE ────────────────────────────────────────
def predict_crowd(location):
    hour = datetime.datetime.now().hour

    # Time-based base device count
    if 12 <= hour <= 14:
        base_devices = random.randint(60, 100)
    elif 17 <= hour <= 20:
        base_devices = random.randint(40, 70)
    elif 8 <= hour <= 10:
        base_devices = random.randint(30, 55)
    else:
        base_devices = random.randint(10, 30)

    # Location-specific multiplier
    multipliers = {
        "Canteen": 1.2,
        "Library": 0.7,
        "Gym": 0.9
    }
    multiplier = multipliers.get(location, 1.0)

    # Live fluctuation
    live_devices = int(base_devices * multiplier) + random.randint(-5, 5)
    live_devices = max(0, live_devices)  # no negatives

    # Crowd level logic
    if live_devices > 70:
        crowd_level = "High"
        wait_time = "15–20 mins"
        color = "red"
    elif live_devices > 40:
        crowd_level = "Medium"
        wait_time = "5–10 mins"
        color = "orange"
    else:
        crowd_level = "Low"
        wait_time = "0–5 mins"
        color = "green"

    # Peak hours info
    peak_hours = {
        "Canteen": "12 PM – 2 PM",
        "Library": "5 PM – 8 PM",
        "Gym": "6 PM – 8 PM"
    }

    # Save to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO crowd_logs (location, device_count, crowd_level, wait_time) VALUES (?, ?, ?, ?)",
        (location, live_devices, crowd_level, wait_time)
    )
    conn.commit()
    conn.close()

    return {
        "location": location,
        "device_count": live_devices,
        "crowd_level": crowd_level,
        "wait_time": wait_time,
        "color": color,
        "peak_hours": peak_hours.get(location, "N/A"),
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S")
    }

# ─── HISTORY FOR GRAPH ────────────────────────────────────────
def get_history(location, limit=12):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT device_count, timestamp FROM crowd_logs WHERE location=? ORDER BY id DESC LIMIT ?",
        (location, limit)
    )
    rows = c.fetchall()
    conn.close()
    rows.reverse()
    return {
        "counts": [r[0] for r in rows],
        "times": [r[1][11:16] for r in rows]  # HH:MM only
    }

# ─── ROUTES ──────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    location = request.args.get("location", "Canteen")
    return render_template("dashboard.html", location=location)

@app.route("/api/crowd")
def api_crowd():
    location = request.args.get("location", "Canteen")
    data = predict_crowd(location)
    return jsonify(data)

@app.route("/api/history")
def api_history():
    location = request.args.get("location", "Canteen")
    data = get_history(location)
    return jsonify(data)

# ─── RUN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("✅ Server running at http://127.0.0.1:5000")
    app.run(debug=True)