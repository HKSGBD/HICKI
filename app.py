from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import threading
import time
import random
from collections import deque
from predictor import predict_next_candle

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

candles_deque = deque(maxlen=20)

def generate_candle(previous_close):
    change = random.uniform(-0.0005, 0.0005)
    open_price = previous_close
    close_price = open_price + change
    high = max(open_price, close_price) + random.uniform(0, 0.0002)
    low = min(open_price, close_price) - random.uniform(0, 0.0002)
    volume = random.randint(500, 2000)
    return {'time': time.time(), 'open': open_price, 'high': high, 'low': low, 'close': close_price, 'volume': volume}

def scraper_thread():
    price = 1.10000
    # প্রথমে কিছু ক্যান্ডেল দিয়ে পূর্ণ কর
    for _ in range(15):
        candle = generate_candle(price)
        candles_deque.append(candle)
        price = candle['close']
    while True:
        candle = generate_candle(price)
        candles_deque.append(candle)
        price = candle['close']
        time.sleep(30)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/latest', methods=['GET'])
def latest():
    if len(candles_deque) < 10:
        return jsonify({'error': 'Insufficient data'}), 503
    return jsonify(list(candles_deque)[-10:])

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'candles' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    prediction = predict_next_candle(data['candles'])
    return jsonify(prediction)

if __name__ == '__main__':
    threading.Thread(target=scraper_thread, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
