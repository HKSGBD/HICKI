let candlesData = [];
let chart;

window.api.onSignal((data) => {
  document.getElementById('action').textContent = data.action;
  document.getElementById('action').style.color = data.action === 'CALL' ? '#3fb950' : '#f85149';
  document.getElementById('confidence').textContent = `Confidence: ${data.confidence.toFixed(1)}%`;
  document.getElementById('reason').textContent = data.reason;
  document.getElementById('last-update').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;

  // যদি ফিচার আসে, তবে চার্ট আপডেট
  if (data.candles) {
    candlesData = data.candles;
    updateChart();
  }
});

function updateChart() {
  // Chart.js দিয়ে লাইন চার্ট (সংক্ষিপ্ত)
  if (!chart) {
    const ctx = document.getElementById('priceChart').getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: { labels: [], datasets: [{ label: 'Close', data: [], borderColor: '#58a6ff' }] }
    });
  }
  const labels = candlesData.map((c,i) => i);
  chart.data.labels = labels;
  chart.data.datasets[0].data = candlesData.map(c => c.close);
  chart.update();
}

function learn(label) {
  window.api.learn(label);
  document.getElementById('learn-status').textContent = 'Learning...';
}

function changePair() {
  const pair = document.getElementById('pair-select').value;
  window.api.onChangePair(pair);
}