import os

# Mapping kategori ke folder template
CATEGORY_MAP = {
    # Restoran & Makanan
    "restoran": "restoran",
    "rumah makan": "restoran",
    "warung": "restoran",
    "warung makan": "restoran",
    "mie ayam": "restoran",
    "bakso": "restoran",
    "seafood": "restoran",

    # Cafe
    "cafe": "cafe",
    "kafe": "cafe",
    "coffee shop": "cafe",
    "kedai kopi": "cafe",
    "kedai": "cafe",

    # Salon & Kecantikan
    "salon": "salon",
    "salon kecantikan": "salon",
    "barbershop": "salon",
    "barber": "salon",
    "spa": "salon",
    "nail art": "salon",

    # Klinik & Kesehatan
    "klinik": "klinik",
    "dokter": "klinik",
    "klinik gigi": "klinik",
    "apotek": "klinik",
    "puskesmas": "klinik",
    "rumah sakit": "klinik",

    # Hotel & Penginapan
    "hotel": "hotel",
    "penginapan": "hotel",
    "homestay": "hotel",
    "villa": "hotel",
    "guest house": "hotel",
    "kost": "hotel",
}

DEFAULT_TEMPLATE = "restoran"
TEMPLATES_DIR = "previews/templates"

class TemplateSelector:
    def get_template_path(self, category: str) -> str:
        category_lower = (category or "").lower().strip()

        template_folder = None
        for key, folder in CATEGORY_MAP.items():
            if key in category_lower:
                template_folder = folder
                break

        if not template_folder:
            template_folder = DEFAULT_TEMPLATE

        template_path = os.path.join(TEMPLATES_DIR, template_folder, "template.html")

        if not os.path.exists(template_path):
            template_path = os.path.join(TEMPLATES_DIR, DEFAULT_TEMPLATE, "template.html")

        return template_path

    def get_template_name(self, category: str) -> str:
        category_lower = (category or "").lower().strip()
        for key, folder in CATEGORY_MAP.items():
            if key in category_lower:
                return folder
        return DEFAULT_TEMPLATE
