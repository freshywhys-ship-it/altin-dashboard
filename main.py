import os
import json
from datetime import datetime
import aiohttp
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

app = FastAPI()

# CORS – tüm originlere izin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Veri Havuzu ----------
veri_havuzu = []                # {"zaman": ISO, "fiyat": float}
MAX_VERI = 500
son_bilinen_fiyat = None
son_bilinen_degisim = 0.0

# ---------- ENDPOINTLER ----------
@app.get("/")
async def root():
    # index.html dosyasını oku ve döndür
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html bulunamadı</h1>", status_code=404)

@app.get("/api/altin")
async def altin():
    global son_bilinen_fiyat, son_bilinen_degisim, veri_havuzu
    try:
        fiyat, degisim = await get_altin_fiyati()
        if fiyat is None:
            if son_bilinen_fiyat is not None:
                fiyat = son_bilinen_fiyat
                degisim = son_bilinen_degisim
            else:
                return JSONResponse({
                    "fiyat": None,
                    "degisim": 0.0,
                    "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "hata": "Veri alınamadı"
                })
        # Havuza ekle
        now = datetime.now().isoformat()
        veri_havuzu.append({"zaman": now, "fiyat": fiyat})
        if len(veri_havuzu) > MAX_VERI:
            veri_havuzu.pop(0)
        son_bilinen_fiyat = fiyat
        son_bilinen_degisim = degisim
        return JSONResponse({
            "fiyat": fiyat,
            "degisim": degisim,
            "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        print(f"Altın endpoint hatası: {e}")
        traceback.print_exc()
        if son_bilinen_fiyat is not None:
            return JSONResponse({
                "fiyat": son_bilinen_fiyat,
                "degisim": son_bilinen_degisim,
                "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hata": str(e)
            })
        else:
            return JSONResponse({
                "fiyat": None,
                "degisim": 0.0,
                "guncelleme": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "hata": "Veri alınamadı"
            })

@app.get("/api/gecmis")
async def gecmis():
    return JSONResponse(veri_havuzu[-500:])

# ---------- ALTIN FİYATI ÇEKME (3 API stratejisi) ----------
async def get_altin_fiyati():
    global son_bilinen_fiyat, son_bilinen_degisim

    # 1. Gold-API (birincil)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.gold-api.com/api/v1/latest/XAU/TRY", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Gold-API yanıtı: {data}")
                    fiyat = data.get("price") or data.get("rate")
                    if fiyat is not None:
                        fiyat = float(fiyat)
                        degisim = data.get("change_percent") or data.get("change") or 0.0
                        if isinstance(degisim, str):
                            degisim = float(degisim)
                        return fiyat, degisim
    except Exception as e:
        print(f"Gold-API hatası: {e}")

    # 2. ExchangeRate-API (ikincil) – XAU/USD ve USD/TRY alıp grama çevir
    try:
        async with aiohttp.ClientSession() as session:
            # XAU/USD (ons fiyatı)
            async with session.get("https://api.exchangerate-api.com/v4/latest/XAU", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    usd_rate = data.get("rates", {}).get("USD")
                    if usd_rate is None:
                        raise Exception("XAU/USD alınamadı")
                    # USD/TRY
                    async with session.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10) as resp2:
                        if resp2.status == 200:
                            data2 = await resp2.json()
                            try_rate = data2.get("rates", {}).get("TRY")
                            if try_rate is None:
                                raise Exception("USD/TRY alınamadı")
                            # ons fiyatı * kur = TL/ons, sonra grama çevir (1 ons = 31.1035 g)
                            fiyat = (usd_rate * try_rate) / 31.1035
                            degisim = 0.0
                            return fiyat, degisim
    except Exception as e:
        print(f"ExchangeRate-API hatası: {e}")

    # 3. Alpha Vantage (üçüncül)
    try:
        url = "https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=XAU&to_currency=TRY&apikey=demo"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"Alpha Vantage yanıtı: {data}")
                    rate = data.get("Realtime Currency Exchange Rate", {}).get("5. Exchange Rate")
                    if rate is not None:
                        fiyat = float(rate)
                        degisim = 0.0
                        return fiyat, degisim
    except Exception as e:
        print(f"Alpha Vantage hatası: {e}")

    # Hepsi başarısız – son bilineni döndür
    if son_bilinen_fiyat is not None:
        print("Tüm API'ler başarısız, son bilinen fiyat döndürülüyor.")
        return son_bilinen_fiyat, son_bilinen_degisim
    else:
        print("Tüm API'ler başarısız ve hiç veri yok.")
        return None, 0.0

# Render için port
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
