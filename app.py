"""
app.py

Flask API for real-time candle predictions using Quotex WebSocket.
Endpoints:
1. POST /predict - Predicts next candle action from last 10 candles.
2. GET /latest  - Returns the last 10 real-time candles from the background scraper.

CORS is enabled for all origins.
Background scraper maintains last 20 candles in a deque.

For Render deployment, use gunicorn.
"""

import json
import threading
import time
from collections import deque

from flask import Flask, request, jsonify
from flask_cors import CORS
import websocket

from predictor import predict_next_candle

# ----------------------
# Configuration
# ----------------------
ASSET = "EURUSD"
TIMEFRAME = 30
WS_URL = "wss://quotex.com/socket.io/?EIO=3&transport=websocket"
HEARTBEAT_INTERVAL = 25

# Deque to store last 20 candles
candles_deque = deque(maxlen=20)

# Flask app
app = Flask(__name__)
CORS(app)  # Allow all origins

# ----------------------
# WebSocket scraper
# ----------------------
def on_message(ws, message):
    try:
        if message.startswith("42"):
            payload = message[2:]  # remove '42' prefix
            data = json.loads(payload)
            event = data[0]
            event_data = data[1]

            if event == "candle":
                candle = {
                    "time": event_data.get("time"),
                    "open": event_data.get("open"),
                    "high": event_data.get("high"),
                    "low": event_data.get("low"),
                    "close": event_data.get("close"),
                    "volume": event_data.get("volume")
                }
                candles_deque.append(candle)
    except Exception as e:
        print(f"[ERROR] Failed to parse message: {e}")

def on_error(ws, error):
    print(f"[ERROR] WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    print("[INFO] WebSocket closed. Reconnecting in 5 seconds...")
    time.sleep(5)
    start_ws()  # Reconnect

def on_open(ws):
    print("[INFO] WebSocket connection opened.")

    # Subscribe to candle data
    subscribe_payload = ["subscribe_candles", {"asset": ASSET, "timeframe": TIMEFRAME}]
    ws.send("42" + json.dumps(subscribe_payload))

    # Heartbeat thread to keep connection alive
    def heartbeat():
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            try:
                ws.send("2")  # Socket.IO ping
            except Exception:
                break
    threading.Thread(target=heartbeat, daemon=True).start()

def start_ws():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# Start WebSocket in background thread
threading.Thread(target=start_ws, daemon=True).start()

# ----------------------
# Flask endpoints
# ----------------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data or "candles" not in data:
            return jsonify({"error": "Missing 'candles' in request"}), 400
        candles = data["candles"]
        if not isinstance(candles, list) or len(candles) < 10:
            return jsonify({"error": "Provide a list of at least 10 candles"}), 400

        prediction = predict_next_candle(candles)
        return jsonify(prediction)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/latest", methods=["GET"])
def latest():
    try:
        if len(candles_deque) == 0:
            return jsonify({"error": "No candles received yet"}), 503
        latest_candles = list(candles_deque)[-10:]
        return jsonify({"candles": latest_candles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------
# Main
# ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)