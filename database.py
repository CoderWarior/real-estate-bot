import sqlite3


def save_listing(listing):
    connection = sqlite3.connect("real_estate.db")

    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS listings (
        listing_id TEXT PRIMARY KEY,
        url TEXT,
        title TEXT,
        price REAL,
        currency TEXT,
        area REAL,
        price_per_m2 REAL,
        rooms TEXT,
        location TEXT,
        floor TEXT,
        description TEXT
    )
    """)

    cursor.execute("""
    INSERT OR REPLACE INTO listings (
        listing_id,
        url,
        title,
        price,
        currency,
        area,
        price_per_m2,
        rooms,
        location,
        floor,
        description
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        listing["listing_id"],
        listing["url"],
        listing["title"],
        listing["price"],
        listing["currency"],
        listing["area"],
        listing["price_per_m2"],
        listing["rooms"],
        listing["location"],
        listing["floor"],
        listing["description"]
    ))

    connection.commit()
    connection.close()

    print("Listing saved!")