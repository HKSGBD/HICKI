from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import MasterTraderAgent
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# গ্লোবাল এজেন্ট ইনস্ট্যান্স
agent = MasterTraderAgent()

# এজেন্ট থ্রেড শুরু (একবারই)
import threading
threading.Thread(target=agent.run, daemon=True).start()

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/latest', methods=['GET'])
def latest():
    with agent.lock:
        candles = list(agent.candles)
    if len(candles) < 10:
        return jsonify({'error': 'Insufficient data'}), 503
    return jsonify(candles[-10:])

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data or 'candles' not in data:
        return jsonify({'error': 'Invalid input'}), 400
    signal = agent.predict(data['candles'])
    return jsonify({'action': signal, 'confidence': 95})

@app.route('/signal', methods=['GET'])
def current_signal():
    with agent.lock:
        candles = list(agent.candles)
    if len(candles) < 10:
        return jsonify({'error': 'Not enough data'}), 503
    signal = agent.predict(candles[-10:])
    return jsonify({'action': signal, 'confidence': 95})

@app.route('/trade/start', methods=['POST'])
def start_auto():
    agent.auto_trade = True
    return jsonify({'status': 'started', 'balance': agent.balance})

@app.route('/trade/stop', methods=['POST'])
def stop_auto():
    agent.auto_trade = False
    return jsonify({'status': 'stopped', 'balance': agent.balance})

@app.route('/trade/status', methods=['GET'])
def trade_status():
    return jsonify({
        'auto_trade': agent.auto_trade,
        'balance': round(agent.balance, 2),
        'trade_count': len(agent.trades),
        'last_trades': agent.trades[-5:] if agent.trades else []
    })

@app.route('/trade/history', methods=['GET'])
def trade_history():
    return jsonify(agent.trades)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
