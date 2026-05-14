from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import talib
import joblib
import xgboost as xgb
from sklearn.linear_model import SGDClassifier
import os

app = Flask(__name__)
CORS(app)

# গ্লোবাল মডেল
model = None
classes = np.array([0, 1])  # 0=PUT loss, 1=CALL win

def initialize_model():
    global model
    if os.path.exists('model.pkl'):
        model = joblib.load('model.pkl')
    else:
        model = SGDClassifier(loss='log_loss', warm_start=True)
        # ডামি ফিচার দিয়ে আংশিক ফিট (প্রাথমিক)
        X_dummy = np.random.rand(10, 6)
        y_dummy = np.random.randint(0, 2, 10)
        model.partial_fit(X_dummy, y_dummy, classes=classes)
        joblib.dump(model, 'model.pkl')

initialize_model()

def compute_features(candles):
    df = pd.DataFrame(candles)
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['volume'] = df['volume'].astype(float)
    
    # প্রয়োজনীয় ইন্ডিকেটর
    df['rsi'] = talib.RSI(df['close'], timeperiod=7)
    df['stoch_k'], df['stoch_d'] = talib.STOCH(df['high'], df['low'], df['close'])
    df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
    df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'])
    df['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=10)
    df['willr'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=10)
    df['volume_ma'] = df['volume'].rolling(5).mean()
    
    # ফিচার ভেক্টর (সর্বশেষ সারি)
    last = df.iloc[-1][['rsi','stoch_k','macd_hist','cci','willr','volume_ma']].fillna(0).values.reshape(1, -1)
    return last

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    candles = data['candles']
    if len(candles) < 20:
        return jsonify({'error': 'Need at least 20 candles'}), 400
    
    features = compute_features(candles)
    prob = model.predict_proba(features)[0]
    call_prob = prob[1]  # 1 -> CALL
    put_prob = prob[0]
    action = 'CALL' if call_prob > put_prob else 'PUT'
    confidence = max(call_prob, put_prob) * 100
    
    # কারণ তৈরি (সরলীকৃত)
    rsi = features[0][0]
    if rsi < 30: reason = 'Oversold + '
    elif rsi > 70: reason = 'Overbought + '
    else: reason = 'Neutral RSI + '
    reason += 'AI composite'
    
    return jsonify({
        'action': action,
        'confidence': confidence,
        'reason': reason,
        'candles': candles[-50:]  # চার্টের জন্য পাঠাই
    })

@app.route('/learn', methods=['POST'])
def learn():
    data = request.get_json()
    candles = data['candles']
    label = data['label']  # 0 or 1
    if len(candles) < 20:
        return jsonify({'status': 'insufficient data'}), 400
    features = compute_features(candles)
    global model
    model.partial_fit(features, [label])
    joblib.dump(model, 'model.pkl')
    return jsonify({'status': 'model updated'})

if __name__ == '__main__':
    app.run(port=5000)