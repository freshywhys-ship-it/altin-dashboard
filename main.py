import os
from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

@app.route('/api/gold')
def get_gold_data():
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get("https://api.genelpara.com/embed/altin.json", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            gram = data.get('GA', {})
            return jsonify({
                'success': True,
                'data': {
                    'alis': str(gram.get('alis', '0')),
                    'satis': str(gram.get('satis', '0')),
                    'degisim': str(gram.get('degisim', '0')),
                    'guncelleme': str(gram.get('d_zaman', ''))
                }
            })
    except Exception as e:
        pass

    # Yedek Kaynak
    try:
        res2 = requests.get("https://finans.truncgil.com/today.json", timeout=5)
        d2 = res2.json()
        ga = d2.get('Gram Altın', {})
        return jsonify({
            'success': True,
            'data': {
                'alis': ga.get('Alış', '0'),
                'satis': ga.get('Satış', '0'),
                'degisim': ga.get('Değişim', '0'),
                'guncelleme': d2.get('Update_Date', '')
            }
        })
    except Exception as e2:
        return jsonify({
            'success': False,
            'data': {'alis': '0', 'satis': '0', 'degisim': '0', 'guncelleme': 'Hata'}
        }), 500

@app.route('/')
def index():
    with open('index.html', 'r', encoding='utf-8') as f:
        return render_template_string(f.read())

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
