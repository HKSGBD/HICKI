import random

def predict_next_candle(candles):
    if len(candles) < 3:
        return 'CALL' if random.random() < 0.95 else 'PUT'
    last = candles[-1]
    third_last = candles[-3]
    is_three_red = all(c['close'] < c['open'] for c in candles[-3:])
    is_three_green = all(c['close'] > c['open'] for c in candles[-3:])
    last_body = abs(last['close'] - last['open'])
    last_lower_shadow = (last['close'] > last['open'] and (last['open'] - last['low'])) or (last['close'] - last['low'])
    last_upper_shadow = (last['close'] > last['open'] and (last['high'] - last['close'])) or (last['high'] - last['open'])
    volume_spike = last['volume'] > 1500

    if is_three_red and last_lower_shadow > 2 * last_body and volume_spike:
        return 'CALL'
    if is_three_green and last_upper_shadow > 2 * last_body and volume_spike:
        return 'PUT'
    return 'CALL' if random.random() < 0.95 else 'PUT'
