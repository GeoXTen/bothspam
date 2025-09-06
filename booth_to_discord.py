import os
import requests
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("DISCORD_WEBHOOK")
BOOTH_URL = "https://booth.pm/en/browse/3D%20Models"
EXCHANGE_API = "https://api.exchangerate.host/convert?from=JPY&to=USD"

def get_usd_rate():
    try:
        res = requests.get(EXCHANGE_API)
        data = res.json()
        return data.get("result", 0.0067)  # fallback ~0.0067 USD/JPY
    except:
        return 0.0067

def get_latest_items(rate):
    res = requests.get(BOOTH_URL)
    soup = BeautifulSoup(res.text, "html.parser")

    items = []
    for card in soup.select(".item-card"):
        link_tag = card.select_one("a")
        if not link_tag:
            continue
        link = "https://booth.pm" + link_tag.get("href")
        title = link_tag.get("title", "Unknown Item")

        img_tag = card.find("img")
        img = img_tag["src"] if img_tag else None

        price_tag = card.select_one(".price")
        price_text = price_tag.get_text(strip=True) if price_tag else "Free / Unknown"

        jpy_price = 0
        if "¥" in price_text:
            jpy_price = int("".join(filter(str.isdigit, price_text)))

        usd_price = round(jpy_price * rate, 2) if jpy_price else 0
        price_display = f"¥{jpy_price:,} (~${usd_price})" if jpy_price else price_text

        items.append((title, link, img, price_display))
    return items[:3]  # just latest 3 per run

def send_to_discord(item):
    title, link, img, price = item
    payload = {
        "embeds": [
            {
                "title": title,
                "url": link,
                "description": f"💲 {price}",
                "image": {"url": img},
                "color": 0x2ECC71
            }
        ]
    }
    requests.post(WEBHOOK, json=payload)

if __name__ == "__main__":
    rate = get_usd_rate()
    items = get_latest_items(rate)

    for item in items:
        send_to_discord(item)
