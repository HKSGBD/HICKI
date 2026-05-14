"""
predictor.py

This module provides the function `predict_next_candle(candles)` which analyzes the
last 10 completed 30-second candles and predicts the next market move based on
multiple technical indicators.

Input:
    candles: list of dicts with keys ['open', 'high', 'low', 'close', 'volume']

Output:
    dict: {"action": "CALL"/"PUT"/"WAIT", "confidence": int}
"""

import math

def sma(values, period):
    """Simple Moving Average"""
    if len(values) < period:
        return sum(values)/len(values)
    return sum(values[-period:])/period

def ema(values, period):
    """Exponential Moving Average"""
    if len(values) < period:
        return sma(values, len(values))
    k = 2 / (period + 1)
    ema_prev = sma(values[:period], period)
    for price in values[period:]:
        ema_prev = price * k + ema_prev * (1 - k)
    return ema_prev

def stddev(values, period):
    """Standard deviation of last `period` values"""
    if len(values) < period:
        period_values = values
    else:
        period_values = values[-period:]
    mean = sum(period_values)/len(period_values)
    variance = sum((x - mean)**2 for x in period_values)/len(period_values)
    return math.sqrt(variance)

def rsi(candles, period=7):
    """Relative Strength Index"""
    gains, losses = 0, 0
    closes = [c['close'] for c in candles[-period-1:]]
    for i in range(1, len(closes)):
        delta = closes[i] - closes[i-1]
        if delta > 0:
            gains += delta
        else:
            losses -= delta
    if losses == 0:
        return 100
    rs = gains / losses
    return 100 - (100 / (1 + rs))

def bollinger_bands(candles, period=10, std_factor=1.5):
    closes = [c['close'] for c in candles[-period:]]
    ma = sma(closes, period)
    sd = stddev(closes, period)
    upper = ma + std_factor * sd
    lower = ma - std_factor * sd
    return upper, lower, ma

def volume_ma(candles, period=5):
    volumes = [c['volume'] for c in candles[-period:]]
    return sma(volumes, period)

def stochastic_k(candles, period=5):
    closes = [c['close'] for c in candles[-period:]]
    lows = [c['low'] for c in candles[-period:]]
    highs = [c['high'] for c in candles[-period:]]
    lowest = min(lows)
    highest = max(highs)
    if highest - lowest == 0:
        return 50
    return (closes[-1] - lowest) / (highest - lowest) * 100

def macd(candles, fast=12, slow=26, signal=9):
    closes = [c['close'] for c in candles]
    fast_ema = ema(closes, fast)
    slow_ema = ema(closes, slow)
    macd_line = fast_ema - slow_ema
    # For signal line, use last `signal` macd_line values; approximate with sma here
    return macd_line

def price_change_rate(candles, period=3):
    if len(candles) < period + 1:
        return 0
    old = candles[-period-1]['close']
    new = candles[-1]['close']
    return (new - old) / old * 100

def atr(candles, period=5):
    trs = []
    for i in range(1, len(candles)):
        high = candles[i]['high']
        low = candles[i]['low']
        prev_close = candles[i-1]['close']
        tr = max(high-low, abs(high-prev_close), abs(low-prev_close))
        trs.append(tr)
    return sma(trs[-period:], period)

def is_hammer(candle):
    body = abs(candle['close'] - candle['open'])
    lower_shadow = candle['open'] - candle['low'] if candle['close'] > candle['open'] else candle['close'] - candle['low']
    return lower_shadow > 2 * body

def is_shooting_star(candle):
    body = abs(candle['close'] - candle['open'])
    upper_shadow = candle['high'] - candle['close'] if candle['close'] > candle['open'] else candle['high'] - candle['open']
    return upper_shadow > 2 * body

def is_engulfing(candles):
    if len(candles) < 2:
        return False, False
    prev, curr = candles[-2], candles[-1]
    bullish = curr['close'] > curr['open'] and curr['close'] > prev['open'] and curr['open'] < prev['close']
    bearish = curr['close'] < curr['open'] and curr['close'] < prev['open'] and curr['open'] > prev['close']
    return bullish, bearish

def is_doji(candle):
    body = abs(candle['close'] - candle['open'])
    range_ = candle['high'] - candle['low']
    if range_ == 0:
        return False
    return body / range_ < 0.1

def cci(candles, period=10):
    closes = [c['close'] for c in candles[-period:]]
    highs = [c['high'] for c in candles[-period:]]
    lows = [c['low'] for c in candles[-period:]]
    typical_prices = [(h + l + c)/3 for h,l,c in zip(highs, lows, closes)]
    ma_tp = sma(typical_prices, period)
    mean_dev = sum(abs(tp - ma_tp) for tp in typical_prices)/period
    if mean_dev == 0:
        return 0
    return (typical_prices[-1] - ma_tp) / (0.015 * mean_dev)

def williams_r(candles, period=10):
    highs = [c['high'] for c in candles[-period:]]
    lows = [c['low'] for c in candles[-period:]]
    close = candles[-1]['close']
    highest = max(highs)
    lowest = min(lows)
    if highest - lowest == 0:
        return -50
    return (highest - close)/(highest - lowest) * -100

def predict_next_candle(candles):
    """
    Predicts next candle action based on technical indicators.
    Returns:
        dict: {"action": "CALL"/"PUT"/"WAIT", "confidence": int}
    """
    last = candles[-1]
    rsi_val = rsi(candles)
    upper_bb, lower_bb, bb_ma = bollinger_bands(candles)
    vol_ma = volume_ma(candles)
    stoch = stochastic_k(candles)
    macd_val = macd(candles)
    # Approximate MACD histogram change
    prev_macd = macd(candles[:-1]) if len(candles) > 1 else macd_val
    macd_hist_rising = macd_val - prev_macd > 0
    price_rate = price_change_rate(candles)
    atr_val = atr(candles)
    hammer = is_hammer(last)
    shooting_star = is_shooting_star(last)
    bullish_engulf, bearish_engulf = is_engulfing(candles)
    doji = is_doji(last)
    cci_val = cci(candles)
    will_r = williams_r(candles)

    # Strong rules
    if (rsi_val < 25 and stoch < 15 and last['close'] < lower_bb and hammer and 
        last['volume'] > 1.5 * vol_ma and macd_hist_rising and will_r < -90 and cci_val < -150):
        return {"action": "CALL", "confidence": 95}

    if (rsi_val > 75 and stoch > 85 and last['close'] > upper_bb and shooting_star and 
        last['volume'] > 1.5 * vol_ma and not macd_hist_rising and will_r > -10 and cci_val > 150):
        return {"action": "PUT", "confidence": 95}

    # Secondary weighted scoring
    score = 0
    score += 1 if rsi_val < 50 else -1
    score += 1 if stoch < 50 else -1
    score += 1 if last['close'] < lower_bb else -1
    score += 1 if hammer else -1
    score += 1 if shooting_star else -1
    score += 1 if bullish_engulf else -1
    score += -1 if bearish_engulf else 1
    score += 1 if doji else 0
    score += 1 if cci_val < 0 else -1
    score += 1 if will_r < -50 else -1

    if score > 3:
        return {"action": "CALL", "confidence": 70}
    elif score < -3:
        return {"action": "PUT", "confidence": 70}
    else:
        return {"action": "WAIT", "confidence": 50}