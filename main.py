import os
from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

@app.route('/api/gold')
def get_gold_data():
    try:
        # Doğrudan piyasa verisi sağlayan alternatif endpoint
        url = "https://api.genelpara.com/embed/altin.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/"
        }
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            gram = data.get('GA', {})
            if gram and 'alis' in gram:
                return jsonify({
                    'success': True,
                    'data': {
                        'alis': str(gram.get('alis', '0')),
                        'satis': str(gram.get('satis', '0')),
                        'degisim': str(gram.get('degisim', '0')),
                        'guncelleme': str(gram.get('d_zaman', ''))
                    }
                })
        
        # Eğer genelpara yanıt vermezse alternatif serbest piyasa verisi
        fallback_url = "https://finans.truncgil.com/today.json"
        res2 = requests.get(fallback_url, headers=headers, timeout=5)
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

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {'alis': '0', 'satis': '0', 'degisim': '0', 'guncelleme': 'Hata'}
        }), 500

@app.route('/')
def index():
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return render_template_string(f.read())
    except Exception as e:
        return f"Hata: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
