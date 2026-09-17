import os
import json
import re
import requests

from bs4 import BeautifulSoup
from dotenv import load_dotenv

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

SEARCH_URL = "https://www.pazar3.mk/ads/real-estate/apartments/for-sale/skopje"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_listings():

    response = requests.get(
        SEARCH_URL,
        headers=HEADERS,
        timeout=20
    )

    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    urls = []
    seen = set()

    for link in soup.find_all("a", href=True):

        href = link["href"]

        if "/ad/real-estate/" not in href:
            continue

        if href.startswith("/"):
            url = "https://www.pazar3.mk" + href
        else:
            url = href

        if url not in seen:
            seen.add(url)
            urls.append(url)

    listings = []

    for url in urls[:10]:

        try:

            listing_response = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

            if listing_response.status_code != 200:
                continue

            listing_soup = BeautifulSoup(
                listing_response.text,
                "html.parser"
            )

            scripts = listing_soup.find_all(
                "script",
                type="application/ld+json"
            )

            for script in scripts:

                try:
                    data = json.loads(
                        script.get_text(strip=True)
                    )
                except json.JSONDecodeError:
                    continue

                if data.get("@type") != "Product":
                    continue

                title = data.get("name")
                listing_id = data.get("sku")

                offers = data.get("offers", {})

                price = offers.get("price")
                currency = offers.get("priceCurrency")

                description = data.get(
                    "description",
                    ""
                )

                # Area

                match = re.search(
                    r"(\d+(?:[.,]\d+)?)\s*[МмMm]\s*2",
                    description
                )

                if match:
                    area = float(
                        match.group(1).replace(",", ".")
                    )
                else:
                    area = None

                # Price per m²

                description_lower = description.lower()

                if (
                    "еур/м2" in description_lower
                    or "eur/m2" in description_lower
                    or "е/м2" in description_lower
                ):

                    price_per_m2 = float(price)

                    if area:
                        total_price = round(
                            price_per_m2 * area,
                            2
                        )
                    else:
                        total_price = None

                else:

                    total_price = float(price)

                    if area:
                        price_per_m2 = round(
                            total_price / area,
                            2
                        )
                    else:
                        price_per_m2 = None

                # Floor

                match = re.search(
                    r"(\d+)\s*/\s*\d+\s*(?:kat|кат)",
                    description,
                    re.IGNORECASE
                )

                if match:
                    floor = match.group(1)

                else:

                    match = re.search(
                        r"(\d+)\s*(?:kat|кат)",
                        description,
                        re.IGNORECASE
                    )

                    if match:
                        floor = match.group(1)
                    else:
                        floor = None

                # Location

                location = None

                location_label = listing_soup.find(
                    "span",
                    string=lambda text:
                    text and text.strip() == "Location:"
                )

                if location_label:

                    container = location_label.parent

                    location = (
                        container
                        .get_text(" ", strip=True)
                        .replace("Location:", "")
                        .strip()
                    )

                listings.append({
                    "id": listing_id,
                    "title": title,
                    "price": total_price,
                    "currency": currency,
                    "area": area,
                    "price_per_m2": price_per_m2,
                    "floor": floor,
                    "location": location,
                    "url": url
                })

                break

        except Exception:
            continue

    return listings


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🏠 Real Estate Bot\n\n"
        "Use /search to find properties."
    )


async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [
        ["🏠 Apartments"],
        ["🏡 Houses"],
        ["🌳 Land"],
        ["🏢 Commercial properties"]
    ]

    await update.message.reply_text(
        "🔎 What would you like to search for?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text

    if text == "🏠 Apartments":

        keyboard = [
            ["📍 Skopje"],
            ["📍 Centar"],
            ["📍 Karpoš"],
            ["📍 Aerodrom"],
            ["📍 Kisela Voda"],
            ["📍 Other"]
        ]

        await update.message.reply_text(
            "📍 Choose a location:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    elif text == "📍 Skopje":

        keyboard = [
            ["💰 Up to 50,000 €"],
            ["💰 50,000 - 100,000 €"],
            ["💰 100,000 - 150,000 €"],
            ["💰 150,000 - 200,000 €"],
            ["💰 Over 200,000 €"],
            ["➡️ No price filter"]
        ]

        await update.message.reply_text(
            "💰 Choose a price range:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True
            )
        )

    elif text == "💰 100,000 - 150,000 €":

        await update.message.reply_text(
            "✅ Price range selected: 100,000 - 150,000 €"
        )


def main():

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("search", search)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            button_handler
        )
    )

    print("🤖 Bot is running...")

    application.run_polling()


if __name__ == "__main__":
    main()
