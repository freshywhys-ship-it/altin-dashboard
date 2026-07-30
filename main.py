import os
from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

# Alternatif ve doğrudan çalışan altın API kaynağı
API_URL = "https://api.genelpara.com/embed/altin.json"

@app.route('/api/gold')
def get_gold_data():
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Gram Altın (GA) verisini çek
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
        # Alternatif fallback (Trunçgil yapısını string temizleme ile dene)
        try:
            fallback_res = requests.get("https://finans.truncgil.com/today.json", headers=headers, timeout=10)
            f_data = fallback_res.json()
            ga = f_data.get('Gram Altın', {})
            return jsonify({
                'success': True,
                'data': {
                    'alis': ga.get('Alış', '0').replace('.', '').replace(',', '.'),
                    'satis': ga.get('Satış', '0').replace('.', '').replace(',', '.'),
                    'degisim': ga.get('Değişim', '0%'),
                    'guncelleme': f_data.get('Update_Date', '')
                }
            })
        except Exception as inner_e:
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
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
