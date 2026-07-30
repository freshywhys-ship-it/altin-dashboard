import os
from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

@app.route('/api/gold')
def get_gold_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # Genel Para API
        response = requests.get("https://api.genelpara.com/embed/altin.json", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        gram_altin = data.get('GA', {})
        
        return jsonify({
            'success': True,
            'data': {
                'alis': gram_altin.get('alis', '0'),
                'satis': gram_altin.get('satis', '0'),
                'degisim': gram_altin.get('degisim', '%0.00'),
                'guncelleme': gram_altin.get('d_zaman', '')
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {
                'alis': '0',
                'satis': '0',
                'degisim': '%0',
                'guncelleme': 'Hata'
            }
        }), 500

@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return render_template_string(html_content)
    except Exception as e:
        return f"index.html okunamadı: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
