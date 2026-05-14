const { app, BrowserWindow, ipcMain } = require('electron');
const puppeteer = require('puppeteer-core');
const axios = require('axios');
const path = require('path');

let mainWindow;
let browser;
let page;
let candlesBuffer = [];

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1300,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  mainWindow.loadFile('index.html');
}

async function startQuotexScraper() {
  // Chrome এর path (সিস্টেম অনুযায়ী চেঞ্জ করতে হতে পারে)
  const chromePath = process.platform === 'win32'
    ? 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
    : '/usr/bin/google-chrome';

  browser = await puppeteer.launch({
    headless: "new",
    executablePath: chromePath,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  page = await browser.newPage();
  await page.goto('https://quotex.com/en/demo-trade', { waitUntil: 'networkidle2' });

  // Quotex WebSocket ক্যান্ডেল ইন্টারসেপ্ট
  await page.evaluateOnNewDocument(() => {
    window.candlesBuffer = [];
    const origWS = window.WebSocket;
    window.WebSocket = function(url, protocols) {
      const ws = new origWS(url, protocols);
      if (url.includes('quotex')) {
        ws.addEventListener('message', (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.candle) {
              window.candlesBuffer.push({
                time: msg.candle.time,
                open: msg.candle.open,
                high: msg.candle.high,
                low: msg.candle.low,
                close: msg.candle.close,
                volume: msg.candle.volume || 500
              });
              // buffer সীমিত রাখি (শেষ 200)
              if (window.candlesBuffer.length > 200) {
                window.candlesBuffer = window.candlesBuffer.slice(-100);
              }
            }
          } catch(e) {}
        });
      }
      return ws;
    };
  });

  // প্রতি 30 সেকেন্ডে ব্যাকএন্ডে পাঠিয়ে প্রেডিকশন নেওয়া
  setInterval(async () => {
    const candles = await page.evaluate(() => window.candlesBuffer);
    if (candles && candles.length >= 10) {
      try {
        const response = await axios.post('http://localhost:5000/predict', {
          candles: candles.slice(-20)
        });
        // mainWindow-এ পাঠাই
        mainWindow.webContents.send('signal', response.data);
      } catch (err) {
        console.error('Backend error:', err.message);
      }
    }
  }, 30000);

  // UI থেকে শেখার রিকোয়েস্ট
  ipcMain.on('learn', async (event, { label }) => {
    const candles = await page.evaluate(() => window.candlesBuffer.slice(-20));
    await axios.post('http://localhost:5000/learn', { candles, label });
    event.sender.send('learn-status', 'Model updated');
  });

  // UI থেকে পেয়ার পরিবর্তন
  ipcMain.on('change-pair', async (event, pair) => {
    await page.click('.pair-selector'); // Quotex এর পেয়ার সিলেক্টর (অনুমান)
    await page.type('.pair-search', pair);
    await page.keyboard.press('Enter');
  });
}

app.whenReady().then(() => {
  createWindow();
  startQuotexScraper();
});

app.on('window-all-closed', () => {
  if (browser) browser.close();
  app.quit();
});