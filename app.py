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

# শেষ 20টি ক্যান্ডেল রাখার জন্য ডেক (deque)
candles_deque = deque(maxlen=20)

def generate_candle(previous_close):
    """একটি 30-সেকেন্ডের ক্যান্ডেল বানায়।"""
    change = random.uniform(-0.0005, 0.0005)
    open_price = previous_close
    close_price = open_price + change
    high = max(open_price, close_price) + random.uniform(0, 0.0002)
    low = min(open_price, close_price) - random.uniform(0, 0.0002)
    volume = random.randint(500, 2000)
    candle = {
        'time': time.time(),
        'open': open_price,
        'high': high,
        'low': low,
        'close': close_price,
        'volume': volume
    }
    return candle

def scraper_thread():
    """ব্যাকগ্রাউন্ডে 30 সেকেন্ড পর পর ক্যান্ডেল জেনারেট করে deque-তে জমা করে।"""
    price = 1.10000
    # প্রথমে 15টি ক্যান্ডেল দিয়ে deque ভরে ফেলি, যাতে /latest ফাঁকা না থাকে
    for _ in range(15):
        candle = generate_candle(price)
        candles_deque.append(candle)
        price = candle['close']
    while True:
        candle = generate_candle(price)
        candles_deque.append(candle)
        price = candle['close']
        time.sleep(30)  # 30 সেকেন্ড অপেক্ষা

# হোমপেজে index.html দেখাবে
@app.route('/')
def index():
    return app.send_static_file('index.html')

# সর্বশেষ 10টি ক্যান্ডেল JSON আকারে দেবে
@app.route('/latest', methods=['GET'])
def latest():
    if len(candles_deque) < 10:
        return jsonify({'error': 'Insufficient data'}), 503
    return jsonify(list(candles_deque)[-10:])

# প্রেডিকশন চাওয়ার API
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'candles' not in data:
        return jsonify({'error': 'Invalid input. Provide { "candles": [...] }'}), 400
    prediction = predict_next_candle(data['candles'])
    return jsonify(prediction)

if __name__ == '__main__':
    # ব্যাকগ্রাউন্ড স্ক্র্যাপার থ্রেড শুরু কর
    threading.Thread(target=scraper_thread, daemon=True).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
