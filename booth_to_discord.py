import os
import requests
from bs4 import BeautifulSoup

WEBHOOK = os.getenv("DISCORD_WEBHOOK")

def get_usd_rate():
    try:
        res = requests.get("https://api.exchangerate.host/latest?base=JPY&symbols=USD", timeout=10)
        data = res.json()
        rate = data["rates"]["USD"]
        print(f"DEBUG: Exchange rate fetched successfully → 1 JPY = {rate:.4f} USD")
        return rate
    except Exception as e:
        print("ERROR: Failed to fetch exchange rate:", e)
        return 0.007  # fallback rate

def get_latest_items(rate):
    url = "https://booth.pm/en/browse/3D%20Models?sort=new"
    print(f"DEBUG: Fetching Booth.pm items from {url}")
    try:
        res = requests.get(url, timeout=10)
        print(f"DEBUG: Booth.pm HTTP status → {res.status_code}")
        soup = BeautifulSoup(res.text, "html.parser")
        items = []
        for product in soup.select(".gallery-item-card")[:10]:  # only take first 10
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

        print(f"DEBUG: Scraped {len(items)} items from Booth.pm")
        return items
    except Exception as e:
        print("ERROR: Failed to scrape Booth.pm:", e)
        return []

def send_to_discord(item):
    if not WEBHOOK:
        print("ERROR: DISCORD_WEBHOOK is missing! Did you set GitHub secret?")
        return

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
        r = requests.post(WEBHOOK, json=payload, timeout=10)
        if r.status_code == 204:
            print(f"SUCCESS: Posted → {item['title']}")
        else:
            print(f"ERROR: Discord response {r.status_code}: {r.text}")
    except Exception as e:
        print("ERROR: Failed to send to Discord:", e)

if __name__ == "__main__":
    print("=== Booth.pm Discord Bot Starting ===")
    rate = get_usd_rate()
    items = get_latest_items(rate)

    if not items:
        print("WARNING: No items scraped. Maybe Booth.pm layout changed?")
    else:
        for item in items[:5]:  # post only first 5 to avoid spam
            send_to_discord(item)

    print("=== Booth.pm Discord Bot Finished ===")
