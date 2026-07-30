from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dünya Katılım - Canlı Gram Altın Takip</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/chartjs-plugin-zoom/2.0.1/chartjs-plugin-zoom.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; background-color: #121212; color: #e0e0e0; text-align: center; margin: 0; padding: 20px; }
        .card { background: #1e1e1e; padding: 20px; border-radius: 10px; display: inline-block; box-shadow: 0 4px 10px rgba(0,0,0,0.5); margin-bottom: 20px; width: 90%; max-width: 700px; }
        .price { font-size: 28px; font-weight: bold; color: #4caf50; }
        .stats { display: flex; justify-content: space-around; background: #252525; padding: 10px; border-radius: 5px; margin: 10px 0; font-size: 14px; }
        .buttons { margin: 15px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
        .time-btns { display: flex; gap: 5px; }
        button { background: #333; color: #fff; border: 1px solid #555; padding: 8px 15px; cursor: pointer; border-radius: 5px; font-weight: bold; }
        button.active { background: #4caf50; border-color: #4caf50; }
        .btn-reset { background: #d32f2f; border-color: #f44336; font-size: 12px; padding: 8px 12px; }
        canvas { background: #181818; border-radius: 5px; padding: 10px; }
        .hint { font-size: 11px; color: #777; margin-top: 8px; }
        .error-msg { color: #f44336; font-size: 12px; margin-top: 5px; display: none; }
    </style>
</head>
<body>

    <div class="card">
        <h2>Dünya Katılım - Gram Altın Takip</h2>
        <div id="source" style="font-size: 12px; color: #888;">Kaynak: Canlı Piyasa Verisi</div>
        <div class="price" id="alis-fiyat">Bağlanıyor...</div>
        <div>Satış: <span id="satis-fiyat">--</span> | Değişim: <span id="degisim">-%</span></div>
        <div style="font-size: 11px; color: #aaa; margin-top: 5px;" id="guncelleme">Son Güncelleme: --:--:--</div>
        <div id="error-alert" class="error-msg">Canlı veri alınamadı, bağlantı bekleniyor...</div>

        <div class="stats">
            <div>En Düşük: <span id="min-fiyat" style="color:#f44336; font-weight:bold;">-- TL</span></div>
            <div>En Yüksek: <span id="max-fiyat" style="color:#4caf50; font-weight:bold;">-- TL</span></div>
        </div>

        <div class="buttons">
            <div class="time-btns">
                <button class="active" onclick="changeTimeframe('1S', this)">1 Saat</button>
                <button onclick="changeTimeframe('1G', this)">1 Gün</button>
                <button onclick="changeTimeframe('1H', this)">1 Hafta</button>
            </div>
            <button class="btn-reset" onclick="resetZoom()">Zoom Sıfırla</button>
        </div>

        <canvas id="goldChart" width="400" height="220"></canvas>
        <div class="hint">Gerçek Zamanlı Piyasa Takip Ekranı</div>
    </div>

    <script>
        let currentTimeframe = '1S';
        let chart;
        const STORAGE_KEY = 'dunya_katilim_real_gold_v1';

        function getStoredHistory() {
            try {
                let data = localStorage.getItem(STORAGE_KEY);
                if (!data) return { '1S': [], '1G': [], '1H': [] };
                return JSON.parse(data);
            } catch (e) {
                return { '1S': [], '1G': [], '1H': [] };
            }
        }

        function saveStoredHistory(history) {
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
            } catch (e) {
                console.error("Kayıt hatası:", e);
            }
        }

        const ctx = document.getElementById('goldChart').getContext('2d');
        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Gram Altın (TL)',
                    data: [],
                    borderColor: '#4caf50',
                    borderWidth: 2,
                    pointRadius: 2,
                    tension: 0.1,
                    fill: true,
                    backgroundColor: 'rgba(76, 175, 80, 0.05)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { ticks: { color: '#aaa', maxTicksLimit: 8 }, grid: { color: '#222' } },
                    y: { ticks: { color: '#aaa' }, grid: { color: '#222' } }
                },
                plugins: {
                    legend: { display: false },
                    zoom: {
                        zoom: { wheel: { enabled: true }, pinch: { enabled: true }, mode: 'xy' },
                        pan: { enabled: true, mode: 'xy' }
                    }
                }
            }
        });

        function updateChartData() {
            let history = getStoredHistory();
            let records = history[currentTimeframe] || [];
            
            chart.data.labels = records.map(item => item.time);
            chart.data.datasets[0].data = records.map(item => item.price);
            chart.update();

            if (records.length > 0) {
                let prices = records.map(r => r.price);
                let min = Math.min(...prices);
                let max = Math.max(...prices);
                document.getElementById('min-fiyat').innerText = min.toFixed(2) + " TL";
                document.getElementById('max-fiyat').innerText = max.toFixed(2) + " TL";
            }
        }

        function changeTimeframe(tf, btn) {
            currentTimeframe = tf;
            document.querySelectorAll('.time-btns button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateChartData();
            chart.resetZoom();
        }

        function resetZoom() {
            chart.resetZoom();
        }

        function fetchData() {
            fetch('/api/gold')
                .then(response => response.json())
                .then(result => {
                    if(result && result.success) {
                        document.getElementById('error-alert').style.display = 'none';
                        document.getElementById('source').innerText = "Kaynak: " + result.source;
                        document.getElementById('alis-fiyat').innerText = result.alis + " TL";
                        document.getElementById('satis-fiyat').innerText = result.satis + " TL";
                        document.getElementById('degisim').innerText = result.degisim;
                        document.getElementById('guncelleme').innerText = "Son Güncelleme: " + result.guncelleme;

                        let currentPrice = parseFloat(result.alis);
                        if (isNaN(currentPrice)) return;

                        let now = new Date();
                        let timeStr = now.toTimeString().split(' ')[0];

                        let history = getStoredHistory();
                        let records = history[currentTimeframe] || [];
                        
                        let lastRecord = records[records.length - 1];
                        // Sadece yeni bir veri noktası geldiğinde veya fiyat değiştiğinde kaydet
                        if (!lastRecord || lastRecord.price !== currentPrice || records.length === 0) {
                            records.push({ time: timeStr, price: currentPrice });
                            let limits = { '1S': 120, '1G': 500, '1H': 2000 };
                            let limit = limits[currentTimeframe] || 200;
                            if (records.length > limit) records.shift();
                            
                            history[currentTimeframe] = records;
                            saveStoredHistory(history);
                            updateChartData();
                        }
                    } else {
                        document.getElementById('error-alert').style.display = 'block';
                    }
                })
                .catch(err => {
                    console.error("Veri çekme hatası:", err);
                    document.getElementById('error-alert').style.display = 'block';
                });
        }

        updateChartData();
        fetchData();
        setInterval(fetchData, 10000); // Her 10 saniyede bir gerçek piyasayı sorgula
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/gold')
def get_gold_price():
    try:
        # Harem Altın veya alternatif canlı finansal kaynakları sorgulama (Gerçek Piyasa API)
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get("https://hasircularaltin.com/api/prices", headers=headers, timeout=5) # veya genelpara/harem endpointleri
        
        # Daha kararlı çalışan alternatif açık finans veri kaynağı (Kuyumcu/Borsa ortak akış)
        fallback_res = requests.get("https://api.genelpara.com/embed/altin.json", headers=headers, timeout=5)
        
        if fallback_res.status_code == 200:
            data = fallback_res.json()
            if 'GA' in data:
                alis = float(data['GA']['alis'])
                satis = float(data['GA']['satis'])
                degisim = f"%{data['GA']['degisim']}"
                simdi = datetime.now().strftime("%H:%M:%S")
                
                return jsonify({
                    "success": True,
                    "source": "Canlı Borsa / Kuyumcu Akışı",
                    "alis": f"{alis:.2f}",
                    "satis": f"{satis:.2f}",
                    "degisim": degisim,
                    "guncelleme": simdi
                })
        
        raise Exception("Canlı piyasa verisine ulaşılamadı")
    
    except Exception as e:
        # Halka açık sistemlerde yanlış veri basmak yerine hata döndürmek en güvenlisidir.
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)

