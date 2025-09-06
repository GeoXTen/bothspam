import os
import requests
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def get_usd_rate():
    try:
        res = requests.get("https://api.exchangerate.host/latest?base=JPY&symbols=USD")
        data = res.json()
        return data["rates"]["USD"]
    except Exception as e:
        print("ERROR: Failed to fetch exchange rate:", e)
        return 0.007  # fallback rate

def get_latest_items(rate):
    url = "https://booth.pm/en/browse/3D%20Models?sort=new"
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.text, "html.parser")
        items = []
        for product in soup.select(".gallery-item-card"):
            title = product.select_one(".gallery-item-name")
            link = product.get("href")
            image = product.select_one("img")
            price = product.select_one(".gallery-item-price")

            if not (title and link and image and price):
                continue

            try:
                jpy = int(price.text.replace("¥", "").replace(",", "").strip())
            except ValueError:
                continue

            usd = jpy * rate

            items.append({
                "title": title.text.strip(),
                "url": "https://booth.pm" + link,
                "image": image["src"],
                "price": jpy,
                "usd_price": usd
            })
        return items
    except Exception as e:
        print("ERROR: Failed to scrape Booth.pm:", e)
        return []

def send_to_discord(item):
    payload = {
        "embeds": [
            {
                "title": item["title"],
                "url": item["url"],
                "image": {"url": item["image"]},
                "footer": {"text": f"Price: ¥{item['price']} | ${item['usd_price']:.2f}"}
            }
        ]
    }
    try:
        r = requests.post(WEBHOOK, json=payload)
        print(f"Posting: {item['title']}")
        print("Discord response:", r.status_code, r.text)
    except Exception as e:
        print("ERROR: Failed to send to Discord:", e)

if __name__ == "__main__":
    rate = get_usd_rate()
    print("DEBUG: Exchange rate JPY→USD =", rate)

    items = get_latest_items(rate)
    print("DEBUG: Found", len(items), "items")

    for item in items[:5]:  # limit to first 5 to avoid spam
        send_to_discord(item)
