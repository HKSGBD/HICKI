// ==UserScript==
// @name         Quotex Data Sender
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Send 30s candle data to Render backend
// @author       You
// @match        https://quotex.com/*
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(function() {
    'use strict';

    const BACKEND_URL = 'https://hicki.onrender.com/collect'; // তোর Render URL

    let lastCandleTime = 0;

    function getCandles() {
        // Quotex চার্টের ক্যান্ডেল ডেটা DOM থেকে নেওয়া (সিম্পল উপায়)
        let candles = [];
        // এখানে Quotex-এর DOM স্ট্রাকচার অনুযায়ী ক্যান্ডেল বের করতে হবে।
        // সাধারণত chart div-এর ভিতরে SVG বা canvas থাকে। আমরা ট্রায়াল দিয়ে বলছি:
        let chartContainer = document.querySelector('.chart-container');
        if (!chartContainer) return candles;
        // ডামি: আমরা সিরিয়াসলি রিয়েল ডাটা নেওয়ার জন্য Quotex-এর WebSocket ইভেন্ট ধরব।
        // কিন্তু যেহেতু ওটা জটিল, আমরা এখানে সিম্পল পদ্ধতি দিচ্ছি:
        // প্রকৃতপক্ষে, Quotex-এর WebSocket থেকে ডাটা নেওয়ার জন্য নিচের কোড ইউজ করবে।
        // এটা আমরা পরে দিচ্ছি।
    }

    // রিয়েল WebSocket সল্যুশন:
    // Quotex-এর WebSocket গ্লোবালি এক্সপোজড থাকে। আমরা সেটা ওভাররাইড করে ডাটা ধরব।
    const originalWebSocket = window.WebSocket;
    window.WebSocket = function(url, protocols) {
        const ws = new originalWebSocket(url, protocols);
        if (url.includes('quotex.com')) {
            ws.addEventListener('message', function(event) {
                try {
                    let data = JSON.parse(event.data);
                    if (data.candle) {
                        // ক্যান্ডেল ডেটা পেলে সার্ভারে পাঠাই
                        let candle = {
                            time: data.candle.time,
                            open: data.candle.open,
                            high: data.candle.high,
                            low: data.candle.low,
                            close: data.candle.close,
                            volume: data.candle.volume || 1000
                        };
                        GM_xmlhttpRequest({
                            method: "POST",
                            url: BACKEND_URL,
                            headers: {"Content-Type": "application/json"},
                            data: JSON.stringify(candle),
                            onload: function(resp) { console.log('Data sent'); }
                        });
                    }
                } catch(e) {}
            });
        }
        return ws;
    };
})();
