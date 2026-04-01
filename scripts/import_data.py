"""
Garden Solutions Data Import Script
Imports products from Shopify CSV and clients into PostgreSQL.
Runs inside the API Docker container.
"""

import sys
import csv
import re
from decimal import Decimal
from collections import defaultdict

sys.path.insert(0, "/app")

from app.core.database import SessionLocal
from app.models.product import Product
from app.models.sku import SKU
from app.models.client import Client
from app.models.price_tier import PriceTier
from app.models.user import User


SKIP_WORDS = {"premium", "plant", "pot", "pots", "concrete", "trough", "the", "and", "with", "for"}

SIZE_ABBREV = {
    "small": "S",
    "medium": "M",
    "large": "L",
    "extra large": "XL",
    "extra-large": "XL",
}

STYLE_ABBREV = {
    "Standard": "STD",
    "With Tray": "TRY",
    "With Pot Feet": "FT",
}

CLIENT_NAMES = [
    "Adeo/Leroy Merlin South Africa (Pty) Ltd",
    "AE NEL t/a PLANT PLEASURE",
    "Alan Maher",
    "Alicia Coetzee",
    "Alicia Lesch",
    "Allison Van Manen",
    "Arlene Stone interiors",
    "B.T. Decor cc",
    "Bar Events",
    "BBR INVESTMENT HOLDING PTY LTD",
    "Bidvest ExecuFlora JHB",
    "Blend Property 20 (Pty) Ltd",
    "BluePrint Business Corp",
    "Bob Bhaga",
    "Botanical Haven",
    "BROADACRES LANDSCAPES",
    "BUDS AND PETALS PTY LTD",
    "Builders BEX Rynie Conv (S110)",
    "Builders BWH Strubens Valley (B14)",
    "Builders BWH Centurion (B33)",
    "Builders BWH Rivonia New (B50)",
    "Builders BEX Southgate (S114)",
    "Builders BEX Lynnwood (S62)",
    "Builders BEX Wonderpark (S76)",
    "Builders BEX Vredenburg (S127)",
    "Builders BWH Polokwane (B17)",
    "Builders BWH Edenvale (B20)",
    "Builders BEX Hermanus New (S123)",
    "Builders BWH Boksburg New",
    "Builders BWH Faerie Glen (B02)",
    "Builders BWH Midrand (B202)",
    "Builders BWH Rustenburg New (B204)",
    "Builders BWH Silver Lakes (B205)",
    "Builders BWH Gezina New (B207)",
    "Builders BWH Glen Eagles (B25)",
    "Builders BWH Bloemfontein (B27)",
    "Builders BEX Nelspruit (B30)",
    "Builders BWH Nelspruit (B30)",
    "Builders BWH Northriding (B31)",
    "Builders BWH Riverhorse (B35)",
    "Builders BWH Woodlands (B36)",
    "Builders BWH Emalahleni (B37)",
    "Builders BEX Middleburg (B39)",
    "Builders BWH Tableview (B41)",
    "Builders BWH Newcastle (B48)",
    "Builders BWH Secunda (B49)",
    "Builders BEX Rossburgh Conv (M053)",
    "Builders BEX Sunward (S115)",
    "Builders BEX Durban North (S117)",
    "Builders BEX Pinetown New (S118)",
    "Builders BEX Ballito (S131)",
    "Builders BEX Beacon Bay (S140)",
    "Builders BEX Cherry Lane (S148)",
    "Builders BEX Hillcrest (S56)",
    "Builders BEX Mahikeng (S57)",
    "Builders Cedar Square (S70)",
    "Builders BEX Greenstone (S75)",
    "Builders BEX Robindale (S78)",
    "Builders East London (S80)",
    "Burgess Landscapes Coastal (Pty) Ltd",
    "C-Pac Co Packers",
    "Calvin",
    "Catherine Van Zuydam",
    "CHAMP",
    "Charmaine Bosch",
    "Cheryl's Landscaping",
    "Christo Mentz",
    "Cleopatra Silaule",
    "Coenique Landscaping",
    "Collen Dlamini",
    "CONCRETE & GARDEN CREATIONS",
    "Corrie Barnard",
    "Create a Landscape",
    "CRISANRA",
    "Dargan Bland Holding Trust",
    "DHEV",
    "Dino Leao",
    "Dona",
    "Dr Neermala Dasi",
    "Dr Van De Merwe",
    "DUSHEN NAIDOO",
    "ECKARDS GARDEN PAVILION",
    "ENGEN TOM CAMPHER MOTORS",
    "Exclusive Landscapes",
    "Fourways Airconditioning Cape (PTY) Ltd",
    "Fresh Earth Gardens",
    "FYNBOS LANDSCAPES",
    "Garden Heart cc",
    "Garden Mechanix",
    "GARDEN VALE",
    "GARDENSHOP PARKTOWN",
    "GOODIES FOR GARDENS KEMPTON PARK",
    "Graces Glory",
    "GRANT ADAM",
    "Greenery Guru",
    "Hadland Business Pty Ltd t/a Working Hands",
    "HILLCREST NURSERY",
    "Hingham Nursery",
    "Ilani",
    "IN EEDEN DESIGN CONCEPTS",
    "INDIGO NURSERY",
    "Inkanyezi Green",
    "Jane E. Franklin",
    "JD MALAN t/a MALANSEUNS PLESIER PLANTE",
    "JeanGreen Landscaping",
    "Johannes du Preez",
    "Jonathan Gunthorp",
    "JUST FABULOUS LANDSCAPING",
    "Karen Gardelli T/A Creative Containers",
    "Karin Conradie",
    "Keen Gro",
    "KIM DAWSON",
    "Kooigoed (Pty) Ltd",
    "Kylie van Zyl",
    "LAMNA FINANCIAL (PTY) LTD",
    "Landscape Inspirations",
    "Leon Arangies",
    "Life Green Group t/a Life Indoors",
    "LIFESTYLE GARDEN CENTRE (PTY) LTD",
    "Lindsay Frederiksen",
    "Livinggreen Landscapes",
    "LOTS OF POTS",
    "LOTS OF POTS BOKSBURG",
    "LOTS OF POTS CENTURION",
    "MACAL FARMS CC",
    "MAGIC GARDEN CENTRE",
    "Matt Durrans Dr",
    "Mellissa Susan",
    "Metropolitan shop UG40 Shoshanguve Mall",
    "MICA BALLITO",
    "Michael Power",
    "MONKEY FOUNTAIN NURSERY",
    "MONTROSE NURSERY",
    "Mpume Takalani",
    "Munka Projects (Pty) Ltd",
    "Mustardtree Landscapers",
    "Mustardtree Landscapes",
    "Nature Blueprint Horticulture",
    "NATURES WAY LANDSCAPING",
    "Nicholas Cloete",
    "NICOLAS PLANTS",
    "NORDIC LIGHT PROPERTIES",
    "Orange Films",
    "Perfect Settings Landscaping",
    "PETER G PROJECTS",
    "PLANT PARADISE",
    "Planting for wild life",
    "Pot & Planter (Pty) Ltd t/a The Pot Shack",
    "Pot and Planter",
    "PRETTY GARDENS",
    "Priscilla Jordan",
    "RETSINI NURSERY",
    "Richard Brueton-Firefly Landscaping",
    "Richard Chauke",
    "Richard Honeyman",
    "RYAN NURSERIES",
    "Ryans Nursery",
    "SAFARI GARDEN CENTRE",
    "SALOME Van der Merwe",
    "SAMAGABA PRIVATE LODGE",
    "Sarah Shainfeld",
    "Sarahlda Scott",
    "SCHAFFLER'S GARDEN NURSERY & LANSCAPING",
    "Setters Furniture",
    "Shivana",
    "Simone O'Shea",
    "Stanton Naidoo",
    "Starke Ayres (Rosebank)",
    "Stella Themistocleous",
    "STODELS NURSERIES",
    "SUNKIST GARDEN PAVILION",
    "Sylvia Pass Garden Centre",
    "Tamutsa",
    "Thandi Mbulaheni",
    "The Building Company",
    "The Friendly Plant",
    "The Garden Stone Pvt Ltd",
    "Unlimited Plant Growers",
    "VIRGIN ACTIVE SEA POINT",
    "VOILA SOLUTIONS (PTY) LTD",
    "Walk in Cedar",
    "Walk in",
    "Walk in Church",
    "Walk in DBN",
    "Walk in KZN",
    "Walk in CPT",
    "WATER PLANT CC HARTEBEESPOORT DAM",
    "Westhouse and Garden",
    "Willow Feather Farm",
    "Young Garden Design",
    "Young Landscape Design",
    "YZ GARDENS",
    "Zenberg Landscapes (PTY) LTD",
]


def get_distinctive_word(title: str) -> str:
    """Extract a distinctive word from the product title (up to 5 chars uppercase)."""
    words = re.findall(r'[a-zA-Z]+', title.lower())
    for word in words:
        if word not in SKIP_WORDS and len(word) >= 3:
            return word[:5].upper()
    # Fallback: use first word
    if words:
        return words[0][:5].upper()
    return "PROD"


def get_size_abbrev(size_str: str) -> str:
    """Extract size abbreviation from size string like 'Large | 280mm x 325mm x 715mm'."""
    size_lower = size_str.lower().strip()
    for key, abbrev in SIZE_ABBREV.items():
        if size_lower.startswith(key):
            return abbrev
    # Try to extract first word
    first_word = size_lower.split()[0] if size_lower else ""
    if first_word in ("s", "sm", "small"):
        return "S"
    if first_word in ("m", "md", "med", "medium"):
        return "M"
    if first_word in ("l", "lg", "large"):
        return "L"
    if first_word in ("xl", "extra"):
        return "XL"
    return first_word[:2].upper() or "X"


def get_color_abbrev(color: str) -> str:
    """Generate color abbreviation. Multi-word colors use initials."""
    color = color.strip()
    words = color.split()
    if len(words) > 1:
        return "".join(w[0].upper() for w in words)
    return color[:5].upper() if color else "X"


def get_style_abbrev(style: str) -> str:
    """Get style abbreviation."""
    style = style.strip()
    return STYLE_ABBREV.get(style, style[:3].upper())


def generate_sku_code(product_word: str, size: str, color: str, style: str) -> str:
    """Generate a SKU code like BOLIV-L-AMPER-STD."""
    size_ab = get_size_abbrev(size)
    color_ab = get_color_abbrev(color)
    style_ab = get_style_abbrev(style)
    code = f"{product_word}-{size_ab}-{color_ab}-{style_ab}"
    return code[:50]


def deduplicate_codes(codes: list) -> list:
    """Deduplicate SKU codes by appending -1, -2, etc."""
    seen = {}
    result = []
    for code in codes:
        if code not in seen:
            seen[code] = 0
            result.append(code)
        else:
            seen[code] += 1
            new_code = f"{code}-{seen[code]}"
            result.append(new_code[:50])
    return result


def import_products(db):
    """Import products and SKUs from Shopify CSV."""
    csv_path = "/app/scripts/products_export_1.csv"

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group rows by Handle
    grouped = defaultdict(list)
    for row in rows:
        handle = row.get("Handle", "").strip()
        if handle:
            grouped[handle].append(row)

    product_count = 0
    sku_count = 0
    all_sku_codes = []
    sku_data_list = []

    for handle, product_rows in grouped.items():
        # First row has the product info
        first_row = product_rows[0]
        title = first_row.get("Title", "").strip()
        description = first_row.get("Body (HTML)", "").strip() or None
        category = first_row.get("Type", "").strip() or None
        image_url = first_row.get("Image Src", "").strip() or None

        if not title:
            continue

        product = Product(
            name=title,
            description=description,
            category=category,
            image_url=image_url,
            is_active=True,
        )
        db.add(product)
        db.flush()
        product_count += 1

        product_word = get_distinctive_word(title)

        for row in product_rows:
            size = row.get("Option1 Value", "").strip()
            color = row.get("Option2 Value", "").strip()
            style = row.get("Option3 Value", "").strip() or "Standard"
            price_str = row.get("Variant Price", "0").strip()

            if not size or not color:
                continue

            try:
                price = Decimal(price_str.replace(",", ""))
            except Exception:
                price = Decimal("0")

            code = generate_sku_code(product_word, size, color, style)
            all_sku_codes.append(code)

            if style == "Standard" or not style:
                display_color = color
            else:
                display_color = f"{color} ({style})"

            sku_data_list.append({
                "product_id": product.id,
                "size": size,
                "color": display_color,
                "base_price_rands": price,
            })

    # Deduplicate all SKU codes
    deduped_codes = deduplicate_codes(all_sku_codes)

    for i, sku_data in enumerate(sku_data_list):
        sku = SKU(
            product_id=sku_data["product_id"],
            code=deduped_codes[i],
            size=sku_data["size"],
            color=sku_data["color"],
            base_price_rands=sku_data["base_price_rands"],
            stock_quantity=0,
            is_active=True,
        )
        db.add(sku)
        sku_count += 1

    return product_count, sku_count


def import_clients(db):
    """Import clients with default price tier."""
    default_tier = db.query(PriceTier).filter(PriceTier.name == "Standard").first()
    if not default_tier:
        default_tier = PriceTier(
            name="Standard",
            discount_percentage=Decimal("0.0000"),
            is_active=True,
        )
        db.add(default_tier)
        db.flush()
        print(f"Created 'Standard' price tier (id={default_tier.id})")

    admin_user = db.query(User).filter(User.email == "mikee@dsg.co.za").first()
    if not admin_user:
        admin_user = db.query(User).filter(User.role == "admin").first()
    if not admin_user:
        raise RuntimeError("No admin user found. Please create an admin user first.")

    print(f"Using admin user: {admin_user.email} (id={admin_user.id})")

    client_count = 0
    for name in CLIENT_NAMES:
        existing = db.query(Client).filter(Client.name == name).first()
        if existing:
            continue

        client = Client(
            name=name,
            tier_id=default_tier.id,
            created_by=admin_user.id,
            is_active=True,
        )
        db.add(client)
        client_count += 1

    return client_count


def main():
    print("=" * 60)
    print("Garden Solutions Data Import")
    print("=" * 60)

    db = SessionLocal()
    try:
        print("\n--- Importing Products & SKUs ---")
        product_count, sku_count = import_products(db)
        print(f"Products created: {product_count}")
        print(f"SKUs created: {sku_count}")

        print("\n--- Importing Clients ---")
        client_count = import_clients(db)
        print(f"Clients created: {client_count}")

        db.commit()

        print("\n" + "=" * 60)
        print("IMPORT COMPLETE")
        print(f"  Products: {product_count}")
        print(f"  SKUs:     {sku_count}")
        print(f"  Clients:  {client_count}")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
