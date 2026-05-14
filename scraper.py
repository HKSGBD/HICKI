import json
import time
import websocket
import threading

# User configuration
ASSET = "EURUSD"  # e.g., "EURUSD"
TIMEFRAME = 30    # in seconds
WS_URL = "wss://quotex.com/socket.io/?EIO=3&transport=websocket"

# Heartbeat interval (seconds) to prevent timeout
HEARTBEAT_INTERVAL = 25


def on_message(ws, message):
    """
    Called when a message is received from the server.
    Parses candle updates and prints completed candles as JSON.
    """
    try:
        # Quotex messages are prefixed with '42' for event data
        if message.startswith("42"):
            payload = message[2:]  # remove '42' prefix
            data = json.loads(payload)
            
            # data structure: [event_name, payload]
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
                # Print completed candle as JSON
                print(json.dumps(candle))
    except Exception as e:
        print(f"[ERROR] Failed to parse message: {e}")


def on_error(ws, error):
    print(f"[ERROR] WebSocket error: {error}")


def on_close(ws, close_status_code, close_msg):
    print("[INFO] WebSocket closed. Reconnecting in 5 seconds...")
    time.sleep(5)
    start_ws()


def on_open(ws):
    print("[INFO] WebSocket connection opened.")
    
    # Subscribe to candle data
    # The exact event name and subscription payload depends on Quotex's internal API
    # Example payload structure (may need adjustment based on live API)
    subscribe_payload = ["subscribe_candles", {"asset": ASSET, "timeframe": TIMEFRAME}]
    ws.send("42" + json.dumps(subscribe_payload))

    # Start heartbeat thread to keep connection alive
    def heartbeat():
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            try:
                ws.send("2")  # '2' is ping frame in Socket.IO
            except Exception:
                break

    threading.Thread(target=heartbeat, daemon=True).start()


def start_ws():
    ws = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever()


if __name__ == "__main__":
    print("[INFO] Starting Quotex candle scraper...")
    start_ws()