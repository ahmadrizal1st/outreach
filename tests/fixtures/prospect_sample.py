SAMPLE_PROSPECT = {
    "place_id": "ChIJtest123",
    "name": "Warung Makan Bu Sari",
    "category": "Restoran",
    "subcategory": "Masakan Jawa",
    "address": "Jl. Sudirman No. 12, Surabaya",
    "city": "Surabaya",
    "province": "Jawa Timur",
    "latitude": -7.2575,
    "longitude": 112.7521,
    "phone_raw": "0812-3456-7890",
    "phone_normalized": "6281234567890",
    "website": None,
    "rating": 4.5,
    "review_count": 128,
    "price_level": "$$",
    "is_open": True,
    "source_keyword": "warung makan",
    "source_city": "Surabaya",
    "status": "raw"
}

SAMPLE_PROSPECT_WITH_WEBSITE = {
    **SAMPLE_PROSPECT,
    "place_id": "ChIJtest456",
    "name": "Salon Cantik Mira",
    "category": "Salon",
    "website": "http://saloncantik.com",
    "rating": 4.8,
    "review_count": 203
}
