import requests
from bs4 import BeautifulSoup


URL = "https://www.pazar3.mk/ads/real-estate/apartments/for-sale/skopje"

headers = {
    "User-Agent": "Mozilla/5.0"
}


print("Connecting to Pazar3 search page...")

response = requests.get(
    URL,
    headers=headers,
    timeout=20
)

print("Status code:", response.status_code)

if response.status_code != 200:
    print("Could not access search page.")
    exit()


soup = BeautifulSoup(response.text, "html.parser")

print("Page title:", soup.title.get_text(strip=True))


seen_urls = set()


for link in soup.find_all("a", href=True):

    href = link["href"]

    if "/ad/real-estate/" not in href:
        continue

    if href.startswith("/"):
        full_url = "https://www.pazar3.mk" + href
    else:
        full_url = href

    seen_urls.add(full_url)


print("Listing links found:", len(seen_urls))


for url in seen_urls:

    print("\nOpening listing:")
    print(url)

    listing_response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    print("Listing status:", listing_response.status_code)

    if listing_response.status_code != 200:
        break

    listing_soup = BeautifulSoup(
        listing_response.text,
        "html.parser"
    )

    scripts = listing_soup.find_all(
        "script",
        type="application/ld+json"
    )

    print("JSON-LD scripts found:", len(scripts))

    for script in scripts:

        import json

        try:
            data = json.loads(script.get_text(strip=True))
        except json.JSONDecodeError:
            continue

        if data.get("@type") != "Product":
            continue

        print("Listing ID:", data.get("sku"))
        print("Title:", data.get("name"))

        break

    break
    print(url)