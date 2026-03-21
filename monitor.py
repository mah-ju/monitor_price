from config import AIRBNB_ROOMS, ADULTS, STAY_NIGHTS, PRICE_LIMIT
from airbnb_scraper import get_airbnb_price
from datetime import date, timedelta
from playwright.sync_api import sync_playwright
from notifier import send_telegram
import time
import json
import os


def generate_checkin_dates():
    today = date.today()
    days_ahead = 30
    return [today + timedelta(days=i) for i in range(2, days_ahead)]



def build_airbnb_url(room_id, checkin, checkout):
    return f"https://www.airbnb.com.br/rooms/{room_id}?check_in={checkin}&check_out={checkout}&adults={ADULTS}"



def run():

    checkin_dates = generate_checkin_dates()

    sent = {}
    if os.path.exists("state.json"):
        with open("state.json", "r") as f:
            data = json.load(f)
            sent = data.get("sent", {})

    best_deals = []
    best_price = None

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"])
        page = browser.new_page()

        # =====================
        # 🔵 AIRBNB
        # =====================
        for room in AIRBNB_ROOMS:

            for checkin in checkin_dates:

                checkout = checkin + timedelta(days=STAY_NIGHTS)
                url = build_airbnb_url(room, checkin, checkout)

                price = get_airbnb_price(page, url)
               

                print("Airbnb Room:", room)
                print("Check-in:", checkin)
                print("Price:", price)
                print("URL:", url)

                if price:
                    try:
                        value = price.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        total_price = float(value)

                        if total_price < 200:
                            print("Ignorado (valor muito baixo)")
                            print("------")
                            continue

                        price_per_night = total_price / STAY_NIGHTS

                        if price_per_night <= PRICE_LIMIT:

                            if best_price is None or price_per_night < best_price:
                                best_price = price_per_night
                                best_deals = [{
                                    "source": "airbnb",
                                    "room": room,
                                    "checkin": checkin,
                                    "price": round(price_per_night, 2),
                                    "total_price": total_price,
                                    "url": url
                                }]

                            elif price_per_night == best_price:
                                best_deals.append({
                                    "source": "airbnb",
                                    "room": room,
                                    "checkin": checkin,
                                    "price": round(price_per_night, 2),
                                    "total_price": total_price,
                                    "url": url
                                })

                    except Exception as e:
                        print("Erro Airbnb:", e)

                print("------")

        
        # =====================
        # 📱 ALERTA
        # =====================
        sent_any = False
        new_sent = sent.copy()

        if best_deals:

            for deal in best_deals:

                key = f"{deal['room']}_{deal['checkin']}"
                current_price = deal["price"]

                if key not in sent:
                    should_send = True
                else:
                    old_price = sent[key]
                    should_send = current_price < old_price 
                if not should_send:
                    continue

                message = f"""🔥 MELHOR PREÇO ENCONTRADO!

Fonte: {deal["source"]}
Check-in: {deal["checkin"]}
Diária: R${deal["price"]}
Total: R${deal["total_price"]}

{deal["url"]}
"""

                print(message)
                send_telegram(message)

                new_sent[key] = current_price
                sent_any = True

        with open("state.json", "w") as f:
            json.dump({"sent": new_sent}, f) 

        if not sent_any:
            print("Nenhuma oferta nova encontrada.")
            send_telegram("🔎 Busca realizada.\nNenhuma oferta melhor encontrada.")

        browser.close()


# 🔁 loop automático
if __name__ == "__main__":

    while True:
        run()
        print("\n⏳ Aguardando próxima execução...\n")
        time.sleep(60 * 60 * 4)