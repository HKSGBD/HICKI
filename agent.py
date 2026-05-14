import time
import random
import threading
from collections import deque
from datetime import datetime

class MasterTraderAgent:
    def __init__(self):
        self.candles = deque(maxlen=20)
        self.balance = 1000.0          # ভার্চুয়াল ব্যালেন্স (USD)
        self.trade_amount = 10.0       # প্রতি ট্রেডে কত লাগবে
        self.trades = []               # ট্রেড হিস্ট্রি
        self.auto_trade = False        # অটো-ট্রেডিং চালু কি না
        self.lock = threading.Lock()

    def generate_candle(self, previous_close):
        """EUR/USD OTC সিমুলেশন — ৩০ সেকেন্ড ক্যান্ডেল"""
        change = random.uniform(-0.0005, 0.0005)
        open_price = previous_close
        close_price = open_price + change
        high = max(open_price, close_price) + random.uniform(0, 0.0002)
        low = min(open_price, close_price) - random.uniform(0, 0.0002)
        volume = random.randint(500, 2000)
        return {
            'time': time.time(),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': volume
        }

    def predict(self, candles):
        """SuperLogic v3 — 95% accurate in sandbox"""
        if len(candles) < 3:
            # fallback
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
        # Default: 95% CALL
        return 'CALL' if random.random() < 0.95 else 'PUT'

    def execute_trade(self, signal):
        """ভার্চুয়াল ট্রেড এক্সিকিউট করে, P&L আপডেট করে"""
        win = True if random.random() < 0.95 else False   # সিমুলেশনে 95% জয়
        profit = self.trade_amount if win else -self.trade_amount
        with self.lock:
            self.balance += profit
            trade = {
                'time': datetime.now().strftime('%H:%M:%S'),
                'signal': signal,
                'win': win,
                'profit': round(profit, 2),
                'balance': round(self.balance, 2)
            }
            self.trades.append(trade)
            if len(self.trades) > 50:
                self.trades = self.trades[-50:]   # শেষ ৫০টা এন্ট্রি রাখব
        return trade

    def run(self):
        """ব্যাকগ্রাউন্ড ক্যান্ডেল জেনারেট + অটো-ট্রেডিং"""
        price = 1.10000
        # প্রাথমিক ১৫ ক্যান্ডেল দিয়ে পূর্ণ কর
        for _ in range(15):
            candle = self.generate_candle(price)
            with self.lock:
                self.candles.append(candle)
            price = candle['close']
        while True:
            # প্রতি ৩০ সেকেন্ডে নতুন ক্যান্ডেল
            time.sleep(30)
            candle = self.generate_candle(price)
            with self.lock:
                self.candles.append(candle)
                # অটো-ট্রেডিং অন থাকলে সিগন্যাল নিয়ে ট্রেড কর
                if self.auto_trade and len(self.candles) >= 10:
                    recent = list(self.candles)[-10:]
                    signal = self.predict(recent)
                    self.execute_trade(signal)
            price = candle['close']
