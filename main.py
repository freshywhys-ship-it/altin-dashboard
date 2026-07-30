import os
from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

# Finans Truncgil API adresi
API_URL = "https://finans.truncgil.com/today.json"

@app.route('/api/gold')
def get_gold_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Gram Altın verisini çek
        gram_altin = data.get('Gram Altın', {})
        
        return jsonify({
            'success': True,
            'data': {
                'alis': gram_altin.get('Alış', '0'),
                'satis': gram_altin.get('Satış', '0'),
                'degisim': gram_altin.get('Değişim', '0%'),
                'guncelleme': data.get('Update_Date', '')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except Exception as e:
        return f"index.html okunurken hata oluştu: {str(e)}", 500

if __name__ == '__main__':
    # Render portalının dinamik port ataması için PORT ortam değişkenini dinler
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
