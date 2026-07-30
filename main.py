import json
import os
from datetime import datetime
from flask import Flask, jsonify, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

HISTORY_FILE = "history.json"


def load_history():
  if os.path.exists(HISTORY_FILE):
    try:
      with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except:
      pass
  return {"1S": [], "1G": [], "1H": []}


def save_history(history):
  try:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
      json.dump(history, f, ensure_ascii=False, indent=4)
  except:
    pass


# Sunucu açıldığında geçmişi yükle
gold_history = load_history()


def fetch_from_genelpara():
  try:
    url = "https://www.genelpara.com/altin-fiyatlari/gram-altin/"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=5)
    if response.status_code == 200:
      soup = BeautifulSoup(response.text, "html.parser")
      alis = (
          soup.find("span", {"id": "lblAlis"}).text.strip().replace(",", ".")
      )
      satis = (
          soup.find("span", {"id": "lblSatis"}).text.strip().replace(",", ".")
      )
      degisim = (
          soup.find("span", {"id": "lblDegisim"}).text.strip().replace(",", ".")
      )
      return {
          "success": True,
          "source": "Canlı (GenelPara)",
          "data": {
              "alis": alis,
              "satis": satis,
              "degisim": degisim,
              "guncelleme": datetime.now().strftime("%H:%M:%S"),
          },
      }
  except Exception as e:
    print("API Hatası:", e)
  return None


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/api/gold")
def api_gold():
  result = fetch_from_genelpara()
  if not result:
    # Yedek simülasyon verisi
    result = {
        "success": True,
        "source": "Simülasyon",
        "data": {
            "alis": "6252.80",
            "satis": "6275.30",
            "degisim": "%0.72",
            "guncelleme": datetime.now().strftime("%H:%M:%S"),
        },
    }

  # Sunucu tarafında geçmişe yeni fiyatı ekle ve kaydet
  alis_num = float(result["data"]["alis"])
  global gold_history

  for tf in ["1S", "1G", "1H"]:
    if not gold_history[tf]:
      gold_history[tf] = [alis_num]
    else:
      if gold_history[tf][-1] != alis_num:
        gold_history[tf].append(alis_num)
        if len(gold_history[tf]) > 50:  # Kayıt sınırı
          gold_history[tf].pop(0)

  save_history(gold_history)
  result["history"] = gold_history
  return jsonify(result)


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000)
