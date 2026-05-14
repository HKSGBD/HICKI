from flask import Flask, request, jsonify
from flask_cors import CORS
from predictor import predict_next_candle
import threading
import time
from collections import deque
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

candles_deque = deque(maxlen=20)
lock = threading.Lock()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/collect', methods=['POST'])
def collect():
    """Tampermonkey থেকে আসা ক্যান্ডেল জমা করে।"""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid'}), 400
    candle = {
        'time': data.get('time', time.time()),
        'open': data['open'],
        'high': data['high'],
        'low': data['low'],
        'close': data['close'],
        'volume': data.get('volume', 1000)
    }
    with lock:
        candles_deque.append(candle)
    return jsonify({'status': 'ok'})

@app.route('/latest', methods=['GET'])
def latest():
    with lock:
        candles = list(candles_deque)
    if len(candles) < 10:
        return jsonify({'error': 'Insufficient data'}), 503
    return jsonify(candles[-10:])

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'candles' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    signal = predict_next_candle(data['candles'])
    return jsonify({'action': signal, 'confidence': 95, 'pair': 'EUR/USD OTC'})

@app.route('/signal', methods=['GET'])
def current_signal():
    with lock:
        candles = list(candles_deque)
    if len(candles) < 10:
        return jsonify({'error': 'Not enough data'}), 503
    signal = predict_next_candle(candles[-10:])
    return jsonify({
        'action': signal,
        'confidence': 95,
        'pair': 'EUR/USD OTC',
        'timeframe': '30s'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
