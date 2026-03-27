"""
Seed script to create initial data for development/testing.

Usage:
    cd apps/api
    python -m scripts.seed_admin
"""
import sys
from pathlib import Path
from decimal import Decimal

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.price_tier import PriceTier
from app.models.client import Client
from app.models.product import Product
from app.models.sku import SKU
from app.models.sales_agent import SalesAgent
from app.models.delivery_team import DeliveryTeam
from app.models.delivery_team_member import DeliveryTeamMember
from app.models.store import Store


def seed_admin_user(db: Session) -> User:
    """Create an admin user if one doesn't exist."""
    admin_email = "admin@gardensolutions.com"

    existing = db.query(User).filter(User.email == admin_email).first()
    if existing:
        print(f"Admin user already exists: {admin_email}")
        return existing

    admin_user = User(
        email=admin_email,
        full_name="System Administrator",
        role=UserRole.ADMIN,
        hashed_password=get_password_hash("admin123"),  # Change in production!
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    print(f"Created admin user: {admin_email} (password: admin123)")
    return admin_user


def seed_test_users(db: Session) -> dict[str, User]:
    """Create test users for each role."""
    users = {}
    test_users = [
        ("sales@gardensolutions.com", "Sales Agent", UserRole.SALES, "sales123"),
        ("manufacturing@gardensolutions.com", "Manufacturing Staff", UserRole.MANUFACTURING, "mfg123"),
        ("delivery@gardensolutions.com", "Delivery Driver", UserRole.DELIVERY, "delivery123"),
    ]

    for email, name, role, password in test_users:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"User already exists: {email}")
            users[role] = existing
            continue

        user = User(
            email=email,
            full_name=name,
            role=role,
            hashed_password=get_password_hash(password),
            is_active=True,
        )
        db.add(user)
        users[role] = user
        print(f"Created test user: {email} (password: {password})")

    db.commit()
    return users


def seed_price_tiers(db: Session) -> dict[str, PriceTier]:
    """Create default price tiers."""
    tiers = {}
    tier_data = [
        ("Tier A", Decimal("0.00")),    # No discount
        ("Tier B", Decimal("0.10")),    # 10% discount
        ("Tier C", Decimal("0.15")),    # 15% discount
        ("Tier D", Decimal("0.20")),    # 20% discount
    ]

    for name, discount in tier_data:
        existing = db.query(PriceTier).filter(PriceTier.name == name).first()
        if existing:
            print(f"Price tier already exists: {name}")
            tiers[name] = existing
            continue

        tier = PriceTier(name=name, discount_percentage=discount)
        db.add(tier)
        tiers[name] = tier
        print(f"Created price tier: {name} ({discount * 100}% discount)")

    db.commit()
    return tiers


def seed_clients(db: Session, tiers: dict[str, PriceTier], admin_user: User, sales_user: User) -> list[Client]:
    """Create real Garden Solutions clients."""
    clients = []
    client_data = [
        ("Pot & Planter (Pty) Ltd t/a The Pot Shack", "Tier A", admin_user, ""),
        ("Adeo/Leroy Merlin South Africa (Pty) Ltd", "Tier B", admin_user, ""),
        ("STODELS NURSERIES", "Tier B", admin_user, ""),
        ("LIFESTYLE GARDEN CENTRE (PTY) LTD", "Tier B", admin_user, ""),
        ("Starke Ayres (Rosebank)", "Tier C", sales_user, ""),
        ("Burgess Landscapes Coastal (Pty) Ltd", "Tier C", sales_user, ""),
        ("ECKARDS GARDEN PAVILION", "Tier A", sales_user, ""),
        ("SAFARI GARDEN CENTRE", "Tier A", sales_user, ""),
        ("Life Green Group t/a Life Indoors", "Tier B", admin_user, ""),
        ("FYNBOS LANDSCAPES", "Tier C", sales_user, ""),
        ("Bidvest ExecuFlora JHB", "Tier B", admin_user, ""),
        ("LOTS OF POTS", "Tier A", sales_user, ""),
        ("Greenery Guru", "Tier C", sales_user, ""),
        ("Coenique Landscaping", "Tier C", sales_user, ""),
        ("GARDENSHOP PARKTOWN", "Tier A", admin_user, ""),
        ("AE NEL t/a PLANT PLEASURE", "Tier B", sales_user, ""),
        ("Arlene Stone interiors", "Tier C", sales_user, ""),
        ("B.T. Decor cc", "Tier C", sales_user, ""),
        ("Bar Events", "Tier C", admin_user, ""),
        ("BBR INVESTMENT HOLDING PTY LTD", "Tier B", admin_user, ""),
        ("Blend Property 20 (Pty) Ltd", "Tier C", admin_user, ""),
        ("BluePrint Business Corp", "Tier C", admin_user, ""),
        ("Botanical Haven", "Tier B", sales_user, ""),
        ("BROADACRES LANDSCAPES", "Tier C", sales_user, ""),
        ("BUDS AND PETALS PTY LTD", "Tier B", admin_user, ""),
        ("CONCRETE & GARDEN CREATIONS", "Tier C", sales_user, ""),
        ("Create a Landscape", "Tier C", sales_user, ""),
        ("Exclusive Landscapes", "Tier C", sales_user, ""),
        ("Fourways Airconditioning Cape (PTY) Ltd", "Tier B", admin_user, ""),
        ("Fresh Earth Gardens", "Tier C", sales_user, ""),
        ("Garden Heart cc", "Tier B", admin_user, ""),
        ("Garden Mechanix", "Tier C", sales_user, ""),
        ("GARDEN VALE", "Tier B", admin_user, ""),
        ("GOODIES FOR GARDENS KEMPTON PARK", "Tier A", admin_user, ""),
        ("Hadland Business Pty Ltd t/a Working Hands", "Tier B", admin_user, ""),
        ("Builders Warehouse Strubens Valley", "Tier A", admin_user, ""),
        ("Builders Warehouse Centurion", "Tier A", admin_user, ""),
        ("Builders Warehouse Rivonia", "Tier A", admin_user, ""),
        ("Builders Express Southgate", "Tier A", admin_user, ""),
        ("Builders Express Lynnwood", "Tier A", admin_user, ""),
        ("Builders Express Wonderpark", "Tier A", admin_user, ""),
        ("Builders Express Vredenburg", "Tier A", admin_user, ""),
        ("Alan Maher", "Tier C", sales_user, ""),
        ("Alicia Coetzee", "Tier C", sales_user, ""),
        ("Alicia Lesch", "Tier C", sales_user, ""),
        ("Allison Van Manen", "Tier C", sales_user, ""),
        ("Bob Bhaga", "Tier C", sales_user, ""),
        ("BRYAN", "Tier C", admin_user, ""),
        ("C-Pac Co Packers", "Tier B", admin_user, ""),
        ("Hadland Business Pty Ltd", "Tier B", admin_user, ""),
    ]

    for name, tier_name, owner, address in client_data:
        existing = db.query(Client).filter(Client.name == name).first()
        if existing:
            needs_update = False
            if existing.created_by != owner.id:
                existing.created_by = owner.id
                needs_update = True
            # Update address if not set
            if not existing.address and address:
                existing.address = address
                needs_update = True
            if needs_update:
                db.add(existing)
                print(f"Updated client: {name}")
            else:
                print(f"Client already exists: {name}")
            clients.append(existing)
            continue

        client = Client(
            name=name,
            tier_id=tiers[tier_name].id,
            created_by=owner.id,
            address=address,
        )
        db.add(client)
        clients.append(client)
        print(f"Created client: {name} (Owner: {owner.role})")

    db.commit()
    return clients


def seed_products_and_skus(db: Session) -> list[Product]:
    """Create real Garden Solutions product catalog from Shopify export."""
    products = []
    product_data = [
        {
            "name": "Premium Bolivia Trough Plant Pot",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("PBOLTRPP-LG-AMP", "Large | 280mm x 325mm x 715mm", "Amper", Decimal("901.00"), 0),
                ("PBOLTRPP-LG-CHR", "Large | 280mm x 325mm x 715mm", "Chryso Black", Decimal("901.00"), 0),
                ("PBOLTRPP-LG-FWH", "Large | 280mm x 325mm x 715mm", "Flinted White", Decimal("901.00"), 0),
                ("PBOLTRPP-LG-GRL", "Large | 280mm x 325mm x 715mm", "Granite light", Decimal("901.00"), 0),
                ("PBOLTRPP-LG-GRD", "Large | 280mm x 325mm x 715mm", "Granite dark", Decimal("901.00"), 0),
                ("PBOLTRPP-LG-ROC", "Large | 280mm x 325mm x 715mm", "Rock", Decimal("901.00"), 0),
            ]
        },
        {
            "name": "Premium Tennessee Concrete pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PTENCPOT-MD-AMP", "Medium  600mm x 640mm", "Amper", Decimal("1548.57"), 0),
                ("PTENCPOT-MD-FWH", "Medium  600mm x 640mm", "Flinted White", Decimal("1548.57"), 0),
                ("PTENCPOT-MD-GRL", "Medium  600mm x 640mm", "Granite light", Decimal("1548.57"), 0),
                ("PTENCPOT-MD-GRD", "Medium  600mm x 640mm", "Granite dark", Decimal("1548.57"), 0),
                ("PTENCPOT-MD-ROC", "Medium  600mm x 640mm", "Rock", Decimal("1548.57"), 0),
                ("PTENCPOT-MD-VEL", "Medium  600mm x 640mm", "Velvet", Decimal("1548.57"), 0),
            ]
        },
        {
            "name": "Premium Chunky Trough Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PCHUTRPP-SM-AMP", "Small | 310mm X 300mm X 600mm", "Amper", Decimal("811.76"), 0),
                ("PCHUTRPP-SM-FWH", "Small | 310mm X 300mm X 600mm", "Flinted White", Decimal("811.76"), 0),
                ("PCHUTRPP-SM-GRD", "Small | 310mm X 300mm X 600mm", "Granite dark", Decimal("811.76"), 0),
                ("PCHUTRPP-SM-GRL", "Small | 310mm X 300mm X 600mm", "Granite light", Decimal("811.76"), 0),
                ("PCHUTRPP-SM-ROC", "Small | 310mm X 300mm X 600mm", "Rock", Decimal("811.76"), 0),
                ("PCHUTRPP-SM-VEL", "Small | 310mm X 300mm X 600mm", "Velvet", Decimal("811.76"), 0),
            ]
        },
        {
            "name": "Premium Tulip Plant Pot",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("PTULPP-SM-AMP", "Small | 510mm X 360mm", "Amper", Decimal("918.29"), 0),
                ("PTULPP-SM-FWH", "Small | 510mm X 360mm", "Flinted White", Decimal("918.29"), 0),
                ("PTULPP-SM-GRA", "Small | 510mm X 360mm", "Granite", Decimal("918.29"), 0),
                ("PTULPP-SM-GRA-2", "Small | 510mm X 360mm", "Granite Sealed", Decimal("918.29"), 0),
                ("PTULPP-SM-ROC", "Small | 510mm X 360mm", "Rock", Decimal("918.29"), 0),
                ("PTULPP-SM-VEL", "Small | 510mm X 360mm", "Velvet", Decimal("918.29"), 0),
            ]
        },
        {
            "name": "Premium Protea Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PPROPP-SM-AMP", "Small | 730mm x 400mm", "Amper", Decimal("885.44"), 0),
                ("PPROPP-SM-FWH", "Small | 730mm x 400mm", "Flinted White", Decimal("804.20"), 0),
                ("PPROPP-SM-GRA", "Small | 730mm x 400mm", "Granite", Decimal("804.20"), 0),
                ("PPROPP-SM-GRA-2", "Small | 730mm x 400mm", "Granite Sealed", Decimal("804.20"), 0),
                ("PPROPP-SM-ROC", "Small | 730mm x 400mm", "Rock", Decimal("804.20"), 0),
                ("PPROPP-SM-VEL", "Small | 730mm x 400mm", "Velvet", Decimal("804.20"), 0),
            ]
        },
        {
            "name": "Premium Windsor Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PWINPP-SM-AMP", "Small | 370mm x 240mm", "Amper", Decimal("449.91"), 0),
                ("PWINPP-SM-FWH", "Small | 370mm x 240mm", "Flinted White", Decimal("449.91"), 0),
                ("PWINPP-SM-GRA", "Small | 370mm x 240mm", "Granite", Decimal("449.91"), 0),
                ("PWINPP-SM-GRA-2", "Small | 370mm x 240mm", "Granite Sealed", Decimal("449.91"), 0),
                ("PWINPP-SM-ROC", "Small | 370mm x 240mm", "Rock", Decimal("449.91"), 0),
                ("PWINPP-SM-VEL", "Small | 370mm x 240mm", "Velvet", Decimal("449.91"), 0),
            ]
        },
        {
            "name": "Premium Colorado Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PCOLPP-710-AMP", "710mm x 590mm", "Amper", Decimal("2438.19"), 0),
                ("PCOLPP-710-FWH", "710mm x 590mm", "Flinted White", Decimal("2438.19"), 0),
                ("PCOLPP-710-GRA", "710mm x 590mm", "Granite", Decimal("2438.19"), 0),
                ("PCOLPP-710-GRA-2", "710mm x 590mm", "Granite Sealed", Decimal("2438.19"), 0),
                ("PCOLPP-710-ROC", "710mm x 590mm", "Rock", Decimal("2438.19"), 0),
                ("PCOLPP-710-VEL", "710mm x 590mm", "Velvet", Decimal("2438.19"), 0),
            ]
        },
        {
            "name": "Premium Iris Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PIRIPP-250-AMP", "Tiny | 250mm x 210mm", "Amper", Decimal("154.15"), 0),
                ("PIRIPP-250-FWH", "Tiny | 250mm x 210mm", "Flinted White", Decimal("154.15"), 0),
                ("PIRIPP-250-GRA", "Tiny | 250mm x 210mm", "Granite", Decimal("154.15"), 0),
                ("PIRIPP-250-GRA-2", "Tiny | 250mm x 210mm", "Granite Sealed", Decimal("154.15"), 0),
                ("PIRIPP-250-ROC", "Tiny | 250mm x 210mm", "Rock", Decimal("154.15"), 0),
                ("PIRIPP-250-VEL", "Tiny | 250mm x 210mm", "Velvet", Decimal("154.15"), 0),
            ]
        },
        {
            "name": "Premium Delia Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PDELPP-SM-AMP", "Small | 640mm X 240mm", "Amper", Decimal("608.83"), 0),
                ("PDELPP-SM-FWH", "Small | 640mm X 240mm", "Flinted White", Decimal("608.83"), 0),
                ("PDELPP-SM-GRA", "Small | 640mm X 240mm", "Granite", Decimal("608.83"), 0),
                ("PDELPP-SM-GRA-2", "Small | 640mm X 240mm", "Granite Sealed", Decimal("608.83"), 0),
                ("PDELPP-SM-ROC", "Small | 640mm X 240mm", "Rock", Decimal("608.83"), 0),
                ("PDELPP-SM-VEL", "Small | 640mm X 240mm", "Velvet", Decimal("608.83"), 0),
            ]
        },
        {
            "name": "Premium Eggin Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PEGGPP-270-ROC", "Mini | 270mm X 230mm", "Rock", Decimal("217.44"), 0),
                ("PEGGPP-270-GRA", "Mini | 270mm X 230mm", "Granite", Decimal("217.44"), 0),
                ("PEGGPP-270-GRA-2", "Mini | 270mm X 230mm", "Granite Sealed", Decimal("217.44"), 0),
                ("PEGGPP-270-AMP", "Mini | 270mm X 230mm", "Amper", Decimal("217.44"), 0),
                ("PEGGPP-270-VEL", "Mini | 270mm X 230mm", "Velvet", Decimal("217.44"), 0),
                ("PEGGPP-270-FWH", "Mini | 270mm X 230mm", "Flinted White", Decimal("217.44"), 0),
            ]
        },
        {
            "name": "Premium Curo Trough Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PCURTRPP-SM-ROC", "Small | 250mm h x 200mm w x 700mm l", "rock", Decimal("976.53"), 0),
                ("PCURTRPP-SM-GRA", "Small | 250mm h x 200mm w x 700mm l", "granite", Decimal("976.53"), 0),
                ("PCURTRPP-SM-GRA-2", "Small | 250mm h x 200mm w x 700mm l", "Granite Sealed", Decimal("976.53"), 0),
                ("PCURTRPP-SM-VEL", "Small | 250mm h x 200mm w x 700mm l", "Velvet", Decimal("976.53"), 0),
                ("PCURTRPP-SM-AMP", "Small | 250mm h x 200mm w x 700mm l", "amper", Decimal("976.53"), 0),
                ("PCURTRPP-SM-FWH", "Small | 250mm h x 200mm w x 700mm l", "Flinted White", Decimal("976.53"), 0),
            ]
        },
        {
            "name": "Premium Egg Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PEGGPP-SM-CHR-2", "Small | 345mm x 395mm", "Chryso Black", Decimal("539.59"), 0),
                ("PEGGPP-SM-ROC-2", "Small | 345mm x 395mm", "Rock", Decimal("539.59"), 0),
                ("PEGGPP-SM-GRA-3", "Small | 345mm x 395mm", "Granite", Decimal("539.59"), 0),
                ("PEGGPP-SM-GRA-4", "Small | 345mm x 395mm", "Granite Sealed", Decimal("539.59"), 0),
                ("PEGGPP-SM-VEL-2", "Small | 345mm x 395mm", "Velvet", Decimal("539.59"), 0),
                ("PEGGPP-SM-AMP-2", "Small | 345mm x 395mm", "Ampler", Decimal("539.59"), 0),
            ]
        },
        {
            "name": "Tudor Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("TUDPP-LG-FWH", "Large | 410mm x 410mm", "flinted white", Decimal("1086.47"), 0),
            ]
        },
        {
            "name": "Symphony Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("SYMPP-LG-FWH", "Large | 460mm x 550mm", "flinted white", Decimal("1229.77"), 0),
            ]
        },
        {
            "name": "African Urn concrete pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("AFRURN-Jumbo-AMP", "Jumbo", "Amper", Decimal("1734.53"), 0),
                ("AFRURN-Jumbo-FWH", "Jumbo", "Flinted White", Decimal("1734.53"), 0),
                ("AFRURN-Jumbo-GRA", "Jumbo", "Granite", Decimal("1734.53"), 0),
                ("AFRURN-Jumbo-GRA-2", "Jumbo", "Granite Sealed", Decimal("1734.53"), 0),
                ("AFRURN-Jumbo-ROC", "Jumbo", "Rock", Decimal("1734.53"), 0),
                ("AFRURN-Jumbo-VEL", "Jumbo", "Velvet", Decimal("1734.53"), 0),
            ]
        },
        {
            "name": "G/S Trough Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("GSTRTY-LG-AMP", "Large", "Amper", Decimal("669.85"), 0),
                ("GSTRTY-LG-FWH", "Large", "Flinted White", Decimal("669.85"), 0),
                ("GSTRTY-LG-GRA", "Large", "Granite", Decimal("669.85"), 0),
                ("GSTRTY-LG-GRA-2", "Large", "Granite Sealed", Decimal("669.85"), 0),
                ("GSTRTY-LG-ROC", "Large", "Rock", Decimal("669.85"), 0),
                ("GSTRTY-LG-VEL", "Large", "Velvet", Decimal("669.85"), 0),
            ]
        },
        {
            "name": "Curo Trough Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("CURTRTY-LG-AMP", "Large | 1170mm x 425mm", "Amper", Decimal("629.83"), 0),
                ("CURTRTY-LG-FWH", "Large | 1170mm x 425mm", "Flinted White", Decimal("629.83"), 0),
                ("CURTRTY-LG-GRA", "Large | 1170mm x 425mm", "Granite", Decimal("629.83"), 0),
                ("CURTRTY-LG-GRA-2", "Large | 1170mm x 425mm", "Granite Sealed", Decimal("629.83"), 0),
                ("CURTRTY-LG-ROC", "Large | 1170mm x 425mm", "Rock", Decimal("629.83"), 0),
                ("CURTRTY-LG-VEL", "Large | 1170mm x 425mm", "Velvet", Decimal("629.83"), 0),
            ]
        },
        {
            "name": "Tulip Trough Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("TULTRTY-LG-AMP", "Large | 620mm x 240mm", "Amper", Decimal("408.62"), 0),
                ("TULTRTY-LG-FWH", "Large | 620mm x 240mm", "Flinted White", Decimal("408.62"), 0),
                ("TULTRTY-LG-GRA", "Large | 620mm x 240mm", "Granite", Decimal("408.62"), 0),
                ("TULTRTY-LG-GRA-2", "Large | 620mm x 240mm", "Granite Sealed", Decimal("408.62"), 0),
                ("TULTRTY-LG-ROC", "Large | 620mm x 240mm", "Rock", Decimal("408.62"), 0),
                ("TULTRTY-LG-VEL", "Large | 620mm x 240mm", "Velvet", Decimal("408.62"), 0),
            ]
        },
        {
            "name": "Drip Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("DRITY-LG-AMP", "Large | 380mm", "Amper", Decimal("129.85"), 0),
                ("DRITY-LG-FWH", "Large | 380mm", "Flinted White", Decimal("129.85"), 0),
                ("DRITY-LG-GRL", "Large | 380mm", "Granite light", Decimal("129.85"), 0),
                ("DRITY-LG-GRA", "Large | 380mm", "Granite Dark Sealed", Decimal("129.85"), 0),
                ("DRITY-LG-ROC", "Large | 380mm", "Rock", Decimal("129.85"), 0),
                ("DRITY-LG-VEL", "Large | 380mm", "Velvet", Decimal("129.85"), 0),
            ]
        },
        {
            "name": "Square Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("SQUTY-LG-AMP", "Large | 600mm", "Amper", Decimal("250.88"), 0),
                ("SQUTY-LG-FWH", "Large | 600mm", "Flinted White", Decimal("250.88"), 0),
                ("SQUTY-LG-GRA", "Large | 600mm", "Granite", Decimal("250.88"), 0),
                ("SQUTY-LG-GRA-2", "Large | 600mm", "Granite Sealed", Decimal("250.88"), 0),
                ("SQUTY-LG-ROC", "Large | 600mm", "Rock", Decimal("250.88"), 0),
                ("SQUTY-LG-VEL", "Large | 600mm", "Velvet", Decimal("250.88"), 0),
            ]
        },
        {
            "name": "Square Tray (Legs)",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("SQUTYLEG-LG-AMP", "Large | 370mm", "Amper", Decimal("498.35"), 0),
                ("SQUTYLEG-LG-FWH", "Large | 370mm", "Flinted White", Decimal("498.35"), 0),
                ("SQUTYLEG-LG-GRA", "Large | 370mm", "Granite", Decimal("498.35"), 0),
                ("SQUTYLEG-LG-GRA-2", "Large | 370mm", "Granite Sealed", Decimal("498.35"), 0),
                ("SQUTYLEG-LG-ROC", "Large | 370mm", "Rock", Decimal("498.35"), 0),
                ("SQUTYLEG-LG-VEL", "Large | 370mm", "Velvet", Decimal("498.35"), 0),
            ]
        },
        {
            "name": "Round Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("ROUTY-MD-AMP", "Medium | 630mm", "Amper", Decimal("626.04"), 0),
                ("ROUTY-MD-FWH", "Medium | 630mm", "Flinted White", Decimal("626.04"), 0),
                ("ROUTY-MD-GRA", "Medium | 630mm", "Granite", Decimal("626.04"), 0),
                ("ROUTY-MD-GRA-2", "Medium | 630mm", "Granite Sealed", Decimal("626.04"), 0),
                ("ROUTY-MD-ROC", "Medium | 630mm", "Rock", Decimal("626.04"), 0),
                ("ROUTY-MD-VEL", "Medium | 630mm", "Velvet", Decimal("626.04"), 0),
            ]
        },
        {
            "name": "Curvy Trough Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("CURTRTY-LG-AMP-2", "Large | 1000mm x 330mm", "Amper", Decimal("357.86"), 0),
                ("CURTRTY-LG-FWH-2", "Large | 1000mm x 330mm", "Flinted White", Decimal("357.86"), 0),
                ("CURTRTY-LG-GRA-3", "Large | 1000mm x 330mm", "Granite", Decimal("357.86"), 0),
                ("CURTRTY-LG-GRA-4", "Large | 1000mm x 330mm", "Granite Sealed", Decimal("357.86"), 0),
                ("CURTRTY-LG-ROC-2", "Large | 1000mm x 330mm", "Rock", Decimal("357.86"), 0),
                ("CURTRTY-LG-VEL-2", "Large | 1000mm x 330mm", "Velvet", Decimal("357.86"), 0),
            ]
        },
        {
            "name": "Chunky Trough Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("CHUTRTY-LG-AMP", "Large | 990mm x 480mm", "Amper", Decimal("629.12"), 0),
                ("CHUTRTY-LG-FWH", "Large | 990mm x 480mm", "Flinted White", Decimal("629.12"), 0),
                ("CHUTRTY-LG-GRA", "Large | 990mm x 480mm", "Granite", Decimal("629.12"), 0),
                ("CHUTRTY-LG-GRA-2", "Large | 990mm x 480mm", "Granite Sealed", Decimal("629.12"), 0),
                ("CHUTRTY-LG-ROC", "Large | 990mm x 480mm", "Rock", Decimal("629.12"), 0),
                ("CHUTRTY-LG-VEL", "Large | 990mm x 480mm", "Velvet", Decimal("629.12"), 0),
            ]
        },
        {
            "name": "Skinny Trough Tray",
            "description": "",
            "category": "Concrete Tray",
            "skus": [
                ("SKITRTY-LG-AMP", "Large | 1000mm x 290mm", "Amper", Decimal("405.88"), 0),
                ("SKITRTY-LG-FWH", "Large | 1000mm x 290mm", "Flinted White", Decimal("405.88"), 0),
                ("SKITRTY-LG-GRA", "Large | 1000mm x 290mm", "Granite", Decimal("405.88"), 0),
                ("SKITRTY-LG-GRA-2", "Large | 1000mm x 290mm", "Granite Sealed", Decimal("405.88"), 0),
                ("SKITRTY-LG-ROC", "Large | 1000mm x 290mm", "Rock", Decimal("405.88"), 0),
                ("SKITRTY-LG-VEL", "Large | 1000mm x 290mm", "Velvet", Decimal("405.88"), 0),
            ]
        },
        {
            "name": "Retro Slim Square Pond",
            "description": "",
            "category": "Pond",
            "skus": [
                ("RETSLISQUPON-LG-AMP", "Large | 720mm x 200mm", "Amper", Decimal("2416.20"), 0),
                ("RETSLISQUPON-LG-FWH", "Large | 720mm x 200mm", "Flinted White", Decimal("2416.20"), 0),
                ("RETSLISQUPON-LG-GRA", "Large | 720mm x 200mm", "Granite", Decimal("2416.20"), 0),
                ("RETSLISQUPON-LG-GRA-2", "Large | 720mm x 200mm", "Granite light Sealed", Decimal("2416.20"), 0),
                ("RETSLISQUPON-LG-ROC", "Large | 720mm x 200mm", "Rock", Decimal("2416.20"), 0),
                ("RETSLISQUPON-LG-VEL", "Large | 720mm x 200mm", "Velvet", Decimal("2416.20"), 0),
            ]
        },
        {
            "name": "Texan Trough",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("TEXTRO-LG-AMP", "Large | 600mm x 90mm", "Amper", Decimal("1019.81"), 0),
                ("TEXTRO-LG-FWH", "Large | 600mm x 90mm", "Flinted White", Decimal("1019.81"), 0),
                ("TEXTRO-LG-GRA", "Large | 600mm x 90mm", "Granite", Decimal("1019.81"), 0),
                ("TEXTRO-LG-GRA-2", "Large | 600mm x 90mm", "Granite Sealed", Decimal("1019.81"), 0),
                ("TEXTRO-LG-ROC", "Large | 600mm x 90mm", "Rock", Decimal("1019.81"), 0),
                ("TEXTRO-LG-VEL", "Large | 600mm x 90mm", "Velvet", Decimal("1019.81"), 0),
            ]
        },
        {
            "name": "Square Pillar Pond",
            "description": "",
            "category": "Pond",
            "skus": [
                ("SQUPILPON-LG-AMP", "Large | 870mm x 260mm", "amper", Decimal("2241.12"), 0),
                ("SQUPILPON-LG-GRD", "Large | 870mm x 260mm", "granite dark", Decimal("2241.12"), 0),
                ("SQUPILPON-LG-BRO", "Large | 870mm x 260mm", "bronze", Decimal("2241.12"), 0),
                ("SQUPILPON-LG-CHR", "Large | 870mm x 260mm", "charcoal", Decimal("2241.12"), 0),
                ("SQUPILPON-LG-CHR-2", "Large | 870mm x 260mm", "chryso black", Decimal("2241.12"), 0),
                ("SQUPILPON-LG-GRL", "Large | 870mm x 260mm", "granite light", Decimal("2241.12"), 0),
            ]
        },
        {
            "name": "Succulent Planter",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("SUCPLA-LG-AMP", "Large | 550mm x 135mm", "amper", Decimal("295.00"), 0),
                ("SUCPLA-LG-ANT", "Large | 550mm x 135mm", "antique rust", Decimal("295.00"), 0),
                ("SUCPLA-LG-BRO", "Large | 550mm x 135mm", "bronze", Decimal("295.00"), 0),
                ("SUCPLA-LG-CHR", "Large | 550mm x 135mm", "charcoal", Decimal("295.00"), 0),
                ("SUCPLA-LG-CHR-2", "Large | 550mm x 135mm", "chryso black", Decimal("295.00"), 0),
                ("SUCPLA-LG-GRA", "Large | 550mm x 135mm", "granite", Decimal("295.00"), 0),
            ]
        },
        {
            "name": "Regency Trough",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("REGTRO-LG-AMP", "Large | 270mm x 330mm x 1260mm", "amper", Decimal("1179.76"), 0),
                ("REGTRO-LG-ANT", "Large | 270mm x 330mm x 1260mm", "antique rust", Decimal("1179.76"), 0),
                ("REGTRO-LG-BRO", "Large | 270mm x 330mm x 1260mm", "bronze", Decimal("1179.76"), 0),
                ("REGTRO-LG-CHR", "Large | 270mm x 330mm x 1260mm", "charcoal", Decimal("1179.76"), 0),
                ("REGTRO-LG-CHR-2", "Large | 270mm x 330mm x 1260mm", "chryso black", Decimal("1179.76"), 0),
                ("REGTRO-LG-GRA", "Large | 270mm x 330mm x 1260mm", "granite", Decimal("1179.76"), 0),
            ]
        },
        {
            "name": "Skinny Trough",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("SKITRO-LG-AMP", "Large | 210mm x 230mm x 980mm", "Amper", Decimal("679.54"), 0),
                ("SKITRO-LG-FWH", "Large | 210mm x 230mm x 980mm", "Flinted White", Decimal("679.54"), 0),
                ("SKITRO-LG-GRA", "Large | 210mm x 230mm x 980mm", "Granite", Decimal("679.54"), 0),
                ("SKITRO-LG-GRA-2", "Large | 210mm x 230mm x 980mm", "Granite Sealed", Decimal("679.54"), 0),
                ("SKITRO-LG-ROC", "Large | 210mm x 230mm x 980mm", "Rock", Decimal("679.54"), 0),
                ("SKITRO-LG-VEL", "Large | 210mm x 230mm x 980mm", "Velvet", Decimal("679.54"), 0),
            ]
        },
        {
            "name": "Tulip Lip Trough",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("TULLIPTRO-LG-AMP", "Large | 500mm x 365mm x 750mm", "Amper", Decimal("1403.06"), 0),
                ("TULLIPTRO-LG-FWH", "Large | 500mm x 365mm x 750mm", "Flinted White", Decimal("1403.06"), 0),
                ("TULLIPTRO-LG-GRA", "Large | 500mm x 365mm x 750mm", "Granite", Decimal("1403.06"), 0),
                ("TULLIPTRO-LG-GRA-2", "Large | 500mm x 365mm x 750mm", "Granite Sealed", Decimal("1403.06"), 0),
                ("TULLIPTRO-LG-ROC", "Large | 500mm x 365mm x 750mm", "Rock", Decimal("1403.06"), 0),
                ("TULLIPTRO-LG-VEL", "Large | 500mm x 365mm x 750mm", "Velvet", Decimal("1403.06"), 0),
            ]
        },
        {
            "name": "Tulip Trough",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("TULTRO-LG-AMP", "Large | 500mm x 320mm x 710mm", "Amper", Decimal("1323.09"), 0),
                ("TULTRO-LG-FWH", "Large | 500mm x 320mm x 710mm", "Flinted White", Decimal("1323.09"), 0),
                ("TULTRO-LG-GRA", "Large | 500mm x 320mm x 710mm", "Granite", Decimal("1323.09"), 0),
                ("TULTRO-LG-GRA-2", "Large | 500mm x 320mm x 710mm", "Granite Sealed", Decimal("1323.09"), 0),
                ("TULTRO-LG-ROC", "Large | 500mm x 320mm x 710mm", "Rock", Decimal("1323.09"), 0),
                ("TULTRO-LG-VEL", "Large | 500mm x 320mm x 710mm", "Velvet", Decimal("1323.09"), 0),
            ]
        },
        {
            "name": "Retro Trough",
            "description": "",
            "category": "Concrete Pots",
            "skus": [
                ("RETTRO-LG-AMP", "Large | 730mm x 330mm x 930mm", "amper", Decimal("2568.30"), 0),
                ("RETTRO-LG-ANT", "Large | 730mm x 330mm x 930mm", "antique rust", Decimal("2568.30"), 0),
                ("RETTRO-LG-BRO", "Large | 730mm x 330mm x 930mm", "bronze", Decimal("2568.30"), 0),
                ("RETTRO-LG-CHR", "Large | 730mm x 330mm x 930mm", "charcoal", Decimal("2568.30"), 0),
                ("RETTRO-LG-CHR-2", "Large | 730mm x 330mm x 930mm", "chryso black", Decimal("2568.30"), 0),
                ("RETTRO-LG-GRA", "Large | 730mm x 330mm x 930mm", "granite", Decimal("2568.30"), 0),
            ]
        },
        {
            "name": "Pongola Concrete Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PONCPOT-890-AMP", "890mm x 580mm", "amper", Decimal("2602.29"), 0),
                ("PONCPOT-890-ANT", "890mm x 580mm", "antique rust", Decimal("2602.29"), 0),
                ("PONCPOT-890-BRO", "890mm x 580mm", "bronze", Decimal("2602.29"), 0),
                ("PONCPOT-890-CHR", "890mm x 580mm", "charcoal", Decimal("2602.29"), 0),
                ("PONCPOT-890-CHR-2", "890mm x 580mm", "chryso black", Decimal("2602.29"), 0),
                ("PONCPOT-890-GRA", "890mm x 580mm", "granite", Decimal("2602.29"), 0),
            ]
        },
        {
            "name": "Plantation Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PLACPOT-LG-AMP", "Large | 730mm x 525mm", "Amper", Decimal("2647.30"), 0),
                ("PLACPOT-LG-FWH", "Large | 730mm x 525mm", "Flinted White", Decimal("2647.30"), 0),
                ("PLACPOT-LG-GRA", "Large | 730mm x 525mm", "Granite", Decimal("2647.30"), 0),
                ("PLACPOT-LG-GRA-2", "Large | 730mm x 525mm", "Granite Sealed", Decimal("2647.30"), 0),
                ("PLACPOT-LG-ROC", "Large | 730mm x 525mm", "Rock", Decimal("2647.30"), 0),
                ("PLACPOT-LG-VEL", "Large | 730mm x 525mm", "Velvet", Decimal("2647.30"), 0),
            ]
        },
        {
            "name": "Pinto Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PINCPOT-LG-AMP", "Large | 950mm X 400mm", "Amper", Decimal("2170.15"), 0),
                ("PINCPOT-LG-FWH", "Large | 950mm X 400mm", "Flinted White", Decimal("2170.15"), 0),
                ("PINCPOT-LG-GRA", "Large | 950mm X 400mm", "Granite", Decimal("2170.15"), 0),
                ("PINCPOT-LG-GRA-2", "Large | 950mm X 400mm", "Granite Sealed", Decimal("2170.15"), 0),
                ("PINCPOT-LG-ROC", "Large | 950mm X 400mm", "Rock", Decimal("2170.15"), 0),
                ("PINCPOT-LG-VEL", "Large | 950mm X 400mm", "Velvet", Decimal("2170.15"), 0),
            ]
        },
        {
            "name": "Pear Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PEACPOT-LG-AMP", "Large | 620mm X 610mm", "amper", Decimal("1513.73"), 0),
                ("PEACPOT-LG-ANT", "Large | 620mm X 610mm", "antique rust", Decimal("1513.73"), 0),
                ("PEACPOT-LG-BRO", "Large | 620mm X 610mm", "bronze", Decimal("1513.73"), 0),
                ("PEACPOT-LG-CHR", "Large | 620mm X 610mm", "charcoal", Decimal("1513.73"), 0),
                ("PEACPOT-LG-CHR-2", "Large | 620mm X 610mm", "chryso black", Decimal("1513.73"), 0),
                ("PEACPOT-LG-GRA", "Large | 620mm X 610mm", "granite", Decimal("1513.73"), 0),
            ]
        },
        {
            "name": "Pafuri Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("PAFCPOT-800-AMP", "800mm x 670mm", "amper", Decimal("2955.95"), 0),
                ("PAFCPOT-800-ANT", "800mm x 670mm", "antique rust", Decimal("2955.95"), 0),
                ("PAFCPOT-800-BRO", "800mm x 670mm", "bronze", Decimal("2955.95"), 0),
                ("PAFCPOT-800-CHR", "800mm x 670mm", "charcoal", Decimal("2955.95"), 0),
                ("PAFCPOT-800-CHR-2", "800mm x 670mm", "chryso black", Decimal("2955.95"), 0),
                ("PAFCPOT-800-GRA", "800mm x 670mm", "granite", Decimal("2955.95"), 0),
            ]
        },
        {
            "name": "Oval Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("OVACPOT-LG-AMP", "Large | 600mm x 700mm", "Amper", Decimal("2366.22"), 0),
                ("OVACPOT-LG-FWH", "Large | 600mm x 700mm", "Flinted White", Decimal("2366.22"), 0),
                ("OVACPOT-LG-GRA", "Large | 600mm x 700mm", "Granite", Decimal("2366.22"), 0),
                ("OVACPOT-LG-GRA-2", "Large | 600mm x 700mm", "Granite Sealed", Decimal("2366.22"), 0),
                ("OVACPOT-LG-ROC", "Large | 600mm x 700mm", "Rock", Decimal("2366.22"), 0),
                ("OVACPOT-LG-VEL", "Large | 600mm x 700mm", "Velvet", Decimal("2366.22"), 0),
            ]
        },
        {
            "name": "Nevada Trough Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("NEVTRCPOT-LG-AMP", "Large | 300mm h x 420mm w x 700mm l", "Amper", Decimal("1263.23"), 0),
                ("NEVTRCPOT-LG-FWH", "Large | 300mm h x 420mm w x 700mm l", "Flinted White", Decimal("1263.23"), 0),
                ("NEVTRCPOT-LG-GRA", "Large | 300mm h x 420mm w x 700mm l", "Granite", Decimal("1263.23"), 0),
                ("NEVTRCPOT-LG-GRA-2", "Large | 300mm h x 420mm w x 700mm l", "Granite Sealed", Decimal("1263.23"), 0),
                ("NEVTRCPOT-LG-ROC", "Large | 300mm h x 420mm w x 700mm l", "Rock", Decimal("1263.23"), 0),
                ("NEVTRCPOT-LG-VEL", "Large | 300mm h x 420mm w x 700mm l", "Velvet", Decimal("1263.23"), 0),
            ]
        },
        {
            "name": "Premium Nevada Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("NEVCPOT-SM-AMP", "Small | 850mm x 440mm", "Amper", Decimal("1594.95"), 0),
                ("NEVCPOT-SM-GRA", "Small | 850mm x 440mm", "Granite", Decimal("1594.95"), 0),
                ("NEVCPOT-SM-GRA-2", "Small | 850mm x 440mm", "Granite Sealed", Decimal("1594.95"), 0),
                ("NEVCPOT-SM-ROC", "Small | 850mm x 440mm", "Rock", Decimal("1594.95"), 0),
                ("NEVCPOT-SM-VEL", "Small | 850mm x 440mm", "Velvet", Decimal("1594.95"), 0),
                ("NEVCPOT-SM-FWH", "Small | 850mm x 440mm", "Flinted White", Decimal("1594.95"), 0),
            ]
        },
        {
            "name": "Nebraska Concrete Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("NEBCPOT-LG-AMP", "Large | 1140mm x 490mm", "Amper", Decimal("3001.70"), 0),
                ("NEBCPOT-LG-FWH", "Large | 1140mm x 490mm", "Flinted White", Decimal("3001.70"), 0),
                ("NEBCPOT-LG-GRA", "Large | 1140mm x 490mm", "Granite", Decimal("3001.70"), 0),
                ("NEBCPOT-LG-GRA-2", "Large | 1140mm x 490mm", "Granite Sealed", Decimal("3001.70"), 0),
                ("NEBCPOT-LG-ROC", "Large | 1140mm x 490mm", "Rock", Decimal("3001.70"), 0),
                ("NEBCPOT-LG-VEL", "Large | 1140mm x 490mm", "Velvet", Decimal("3001.70"), 0),
            ]
        },
        {
            "name": "Monica Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("MONCPOT-LG-FWH", "Large | 590mm x 610mm", "flinted white", Decimal("2479.57"), 0),
                ("MONCPOT-LG-CHR", "Large | 590mm x 610mm", "Chryso Black", Decimal("2479.57"), 0),
                ("MONCPOT-LG-GRA", "Large | 590mm x 610mm", "Granite Dark Smooth", Decimal("2479.57"), 0),
                ("MONCPOT-LG-AMP", "Large | 590mm x 610mm", "Amper", Decimal("2479.57"), 0),
                ("MONCPOT-LG-GRA-2", "Large | 590mm x 610mm", "Granite Rough", Decimal("2479.57"), 0),
                ("MONCPOT-LG-RAW", "Large | 590mm x 610mm", "Raw", Decimal("2479.57"), 0),
            ]
        },
        {
            "name": "Millstone Concrete Pot/Pond",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("MILCPOT-LG-AMP", "Large | 900mm X 400mm", "amper", Decimal("3803.63"), 0),
                ("MILCPOT-LG-ANT", "Large | 900mm X 400mm", "antique rust", Decimal("3803.63"), 0),
                ("MILCPOT-LG-BRO", "Large | 900mm X 400mm", "bronze", Decimal("3803.63"), 0),
                ("MILCPOT-LG-CHR", "Large | 900mm X 400mm", "charcoal", Decimal("3803.63"), 0),
                ("MILCPOT-LG-CHR-2", "Large | 900mm X 400mm", "chryso black", Decimal("3803.63"), 0),
                ("MILCPOT-LG-GRA", "Large | 900mm X 400mm", "granite", Decimal("3803.63"), 0),
            ]
        },
        {
            "name": "Mexican Concrete Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("MEXCPOT-1500-AMP", "Giant | 1500mm X 600mm", "Amper", Decimal("3417.76"), 0),
                ("MEXCPOT-1500-FWH", "Giant | 1500mm X 600mm", "Flinted White", Decimal("3417.76"), 0),
                ("MEXCPOT-1500-GRA", "Giant | 1500mm X 600mm", "Granite", Decimal("3417.76"), 0),
                ("MEXCPOT-1500-GRA-2", "Giant | 1500mm X 600mm", "Granite Sealed", Decimal("3417.76"), 0),
                ("MEXCPOT-1500-ROC", "Giant | 1500mm X 600mm", "Rock", Decimal("3417.76"), 0),
                ("MEXCPOT-1500-VEL", "Giant | 1500mm X 600mm", "Velvet", Decimal("3417.76"), 0),
            ]
        },
        {
            "name": "Lilly Pond Concrete Pond",
            "description": "",
            "category": "Pond",
            "skus": [
                ("LILPONCPOT-LG-AMP", "Large | 400mm x 1240mm", "Amper", Decimal("2586.77"), 0),
                ("LILPONCPOT-LG-FWH", "Large | 400mm x 1240mm", "Flinted White", Decimal("2586.77"), 0),
                ("LILPONCPOT-LG-GRL", "Large | 400mm x 1240mm", "Granite Light", Decimal("2586.77"), 0),
                ("LILPONCPOT-LG-GRD", "Large | 400mm x 1240mm", "Granite Dark", Decimal("2586.77"), 0),
                ("LILPONCPOT-LG-ROC", "Large | 400mm x 1240mm", "Rock", Decimal("2586.77"), 0),
                ("LILPONCPOT-LG-VEL", "Large | 400mm x 1240mm", "Velvet", Decimal("2586.77"), 0),
            ]
        },
        {
            "name": "Kathy Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("KATCPOT-LG-AMP", "Large | 530mm x 555mm", "Amper", Decimal("1052.13"), 0),
                ("KATCPOT-LG-FWH", "Large | 530mm x 555mm", "Flinted White", Decimal("1052.13"), 0),
                ("KATCPOT-LG-GRA", "Large | 530mm x 555mm", "Granite", Decimal("1052.13"), 0),
                ("KATCPOT-LG-GRA-2", "Large | 530mm x 555mm", "Granite Sealed", Decimal("1052.13"), 0),
                ("KATCPOT-LG-ROC", "Large | 530mm x 555mm", "Rock", Decimal("1052.13"), 0),
                ("KATCPOT-LG-VEL", "Large | 530mm x 555mm", "Velvet", Decimal("1052.13"), 0),
            ]
        },
        {
            "name": "Jessica Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("JESCPOT-600-AMP", "Jumbo | 600mm X 710mm", "Amper", Decimal("1566.36"), 0),
                ("JESCPOT-600-FWH", "Jumbo | 600mm X 710mm", "Flinted White", Decimal("1566.36"), 0),
                ("JESCPOT-600-GRA", "Jumbo | 600mm X 710mm", "Granite", Decimal("1566.36"), 0),
                ("JESCPOT-600-GRA-2", "Jumbo | 600mm X 710mm", "Granite Sealed", Decimal("1566.36"), 0),
                ("JESCPOT-600-ROC", "Jumbo | 600mm X 710mm", "Rock", Decimal("1566.36"), 0),
                ("JESCPOT-600-VEL", "Jumbo | 600mm X 710mm", "Velvet", Decimal("1566.36"), 0),
            ]
        },
        {
            "name": "Italia Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("ITACPOT-LG-AMP", "Large | 500mm x 565mm", "Amper", Decimal("1203.11"), 0),
                ("ITACPOT-LG-FWH", "Large | 500mm x 565mm", "Flinted White", Decimal("1203.11"), 0),
                ("ITACPOT-LG-GRA", "Large | 500mm x 565mm", "Granite", Decimal("1203.11"), 0),
                ("ITACPOT-LG-GRA-2", "Large | 500mm x 565mm", "Granite Sealed", Decimal("1203.11"), 0),
                ("ITACPOT-LG-ROC", "Large | 500mm x 565mm", "Rock", Decimal("1203.11"), 0),
                ("ITACPOT-LG-VEL", "Large | 500mm x 565mm", "Velvet", Decimal("1203.11"), 0),
            ]
        },
        {
            "name": "Hyena Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("HYECPOT-LG-AMP", "Large | 670mm x 420mm", "Amper", Decimal("1118.25"), 0),
                ("HYECPOT-LG-FWH", "Large | 670mm x 420mm", "Flinted White", Decimal("1118.25"), 0),
                ("HYECPOT-LG-GRA", "Large | 670mm x 420mm", "Granite", Decimal("1118.25"), 0),
                ("HYECPOT-LG-GRA-2", "Large | 670mm x 420mm", "Granite Sealed", Decimal("1118.25"), 0),
                ("HYECPOT-LG-ROC", "Large | 670mm x 420mm", "Rock", Decimal("1118.25"), 0),
                ("HYECPOT-LG-VEL", "Large | 670mm x 420mm", "Velvet", Decimal("1118.25"), 0),
            ]
        },
        {
            "name": "Honey Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("HONCPOT-LG-AMP", "Large | 460mm X 430mm", "amper", Decimal("645.00"), 0),
                ("HONCPOT-LG-ANT", "Large | 460mm X 430mm", "antique rust", Decimal("645.00"), 0),
                ("HONCPOT-LG-BRO", "Large | 460mm X 430mm", "bronze", Decimal("645.00"), 0),
                ("HONCPOT-LG-CHR", "Large | 460mm X 430mm", "charcoal", Decimal("645.00"), 0),
                ("HONCPOT-LG-CHR-2", "Large | 460mm X 430mm", "chryso black", Decimal("645.00"), 0),
                ("HONCPOT-LG-GRA", "Large | 460mm X 430mm", "granite", Decimal("645.00"), 0),
            ]
        },
        {
            "name": "Geni Concrete Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("GENCPOT-XL-AMP", "Extra Large | 1300mm x 840mm", "amper", Decimal("4538.58"), 0),
                ("GENCPOT-XL-ANT", "Extra Large | 1300mm x 840mm", "antique rust", Decimal("4538.58"), 0),
                ("GENCPOT-XL-BRO", "Extra Large | 1300mm x 840mm", "bronze", Decimal("4538.58"), 0),
                ("GENCPOT-XL-CHR", "Extra Large | 1300mm x 840mm", "charcoal", Decimal("4538.58"), 0),
                ("GENCPOT-XL-CHR-2", "Extra Large | 1300mm x 840mm", "chryso black", Decimal("4538.58"), 0),
                ("GENCPOT-XL-GRA", "Extra Large | 1300mm x 840mm", "granite", Decimal("4538.58"), 0),
            ]
        },
        {
            "name": "Funduzi Pot Concrete",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("FUNCPOT-LG-AMP", "Large | 1500mm x 600mm", "amper", Decimal("2695.00"), 0),
                ("FUNCPOT-LG-ANT", "Large | 1500mm x 600mm", "antique rust", Decimal("2695.00"), 0),
                ("FUNCPOT-LG-BRO", "Large | 1500mm x 600mm", "bronze", Decimal("2695.00"), 0),
                ("FUNCPOT-LG-CHR", "Large | 1500mm x 600mm", "charcoal", Decimal("2695.00"), 0),
                ("FUNCPOT-LG-CHR-2", "Large | 1500mm x 600mm", "chryso black", Decimal("2695.00"), 0),
                ("FUNCPOT-LG-GRA", "Large | 1500mm x 600mm", "granite", Decimal("2695.00"), 0),
            ]
        },
        {
            "name": "Fortuna Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("FORCPOT-620-AMP", "620mm x 580mm", "Amper", Decimal("1139.27"), 0),
                ("FORCPOT-620-FWH", "620mm x 580mm", "Flinted White", Decimal("1139.27"), 0),
                ("FORCPOT-620-GRA", "620mm x 580mm", "Granite", Decimal("1139.27"), 0),
                ("FORCPOT-620-GRA-2", "620mm x 580mm", "Granite Sealed", Decimal("1139.27"), 0),
                ("FORCPOT-620-ROC", "620mm x 580mm", "Rock", Decimal("1139.27"), 0),
                ("FORCPOT-620-VEL", "620mm x 580mm", "Velvet", Decimal("1139.27"), 0),
            ]
        },
        {
            "name": "Premium Estantia Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("ESTCPOT-SM-AMP", "Small | 410mm x 280mm", "Amper", Decimal("377.74"), 0),
                ("ESTCPOT-SM-FWH", "Small | 410mm x 280mm", "Flinted White", Decimal("377.74"), 0),
                ("ESTCPOT-SM-GRA", "Small | 410mm x 280mm", "Granite", Decimal("377.74"), 0),
                ("ESTCPOT-SM-GRA-2", "Small | 410mm x 280mm", "Granite Sealed", Decimal("377.74"), 0),
                ("ESTCPOT-SM-ROC", "Small | 410mm x 280mm", "Rock", Decimal("377.74"), 0),
                ("ESTCPOT-SM-VEL", "Small | 410mm x 280mm", "Velvet", Decimal("377.74"), 0),
            ]
        },
        {
            "name": "Duo Pair Concrete",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("DUOPAICON-LG-AMP", "Large", "amper", Decimal("6242.45"), 0),
                ("DUOPAICON-LG-ANT", "Large", "antique rust", Decimal("6242.45"), 0),
                ("DUOPAICON-LG-BRO", "Large", "bronze", Decimal("6242.45"), 0),
                ("DUOPAICON-LG-CHR", "Large", "charcoal", Decimal("6242.45"), 0),
                ("DUOPAICON-LG-CHR-2", "Large", "chryso black", Decimal("6242.45"), 0),
                ("DUOPAICON-LG-GRA", "Large", "granite", Decimal("6242.45"), 0),
            ]
        },
        {
            "name": "Cycad Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("CYCCPOT-970-AMP", "970mm x 540mm", "Amper", Decimal("2358.62"), 0),
                ("CYCCPOT-970-FWH", "970mm x 540mm", "Flinted White", Decimal("2358.62"), 0),
                ("CYCCPOT-970-GRA", "970mm x 540mm", "Granite", Decimal("2358.62"), 0),
                ("CYCCPOT-970-GRA-2", "970mm x 540mm", "Granite Sealed", Decimal("2358.62"), 0),
                ("CYCCPOT-970-ROC", "970mm x 540mm", "Rock", Decimal("2358.62"), 0),
                ("CYCCPOT-970-VEL", "970mm x 540mm", "Velvet", Decimal("2358.62"), 0),
            ]
        },
        {
            "name": "Cube Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("CUBCPOT-LG-AMP", "Large | 500mm x 500mm x 500mm", "Amper", Decimal("1298.26"), 0),
                ("CUBCPOT-LG-FWH", "Large | 500mm x 500mm x 500mm", "Flinted White", Decimal("1298.26"), 0),
                ("CUBCPOT-LG-GRA", "Large | 500mm x 500mm x 500mm", "Granite", Decimal("1298.26"), 0),
                ("CUBCPOT-LG-GRA-2", "Large | 500mm x 500mm x 500mm", "Granite Sealed", Decimal("1298.26"), 0),
                ("CUBCPOT-LG-ROC", "Large | 500mm x 500mm x 500mm", "Rock", Decimal("1298.26"), 0),
                ("CUBCPOT-LG-VEL", "Large | 500mm x 500mm x 500mm", "Velvet", Decimal("1298.26"), 0),
            ]
        },
        {
            "name": "Constantia Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("CONCPOT-MD-AMP", "Medium | 480mm x 620mm", "Amper", Decimal("1360.41"), 0),
                ("CONCPOT-MD-FWH", "Medium | 480mm x 620mm", "Flinted White", Decimal("1360.41"), 0),
                ("CONCPOT-MD-GRA", "Medium | 480mm x 620mm", "Granite", Decimal("1360.41"), 0),
                ("CONCPOT-MD-GRA-2", "Medium | 480mm x 620mm", "Granite Sealed", Decimal("1360.41"), 0),
                ("CONCPOT-MD-ROC", "Medium | 480mm x 620mm", "Rock", Decimal("1360.41"), 0),
                ("CONCPOT-MD-VEL", "Medium | 480mm x 620mm", "Velvet", Decimal("1360.41"), 0),
            ]
        },
        {
            "name": "Premium Clermont Trough Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("CLETRCPOT-SM-AMP", "Small | 270mm h x 310mm w x 600mm l", "Amper", Decimal("809.21"), 0),
                ("CLETRCPOT-SM-FWH", "Small | 270mm h x 310mm w x 600mm l", "Flinted White", Decimal("809.21"), 0),
                ("CLETRCPOT-SM-GRA", "Small | 270mm h x 310mm w x 600mm l", "Granite", Decimal("809.21"), 0),
                ("CLETRCPOT-SM-GRA-2", "Small | 270mm h x 310mm w x 600mm l", "Granite Sealed", Decimal("809.21"), 0),
                ("CLETRCPOT-SM-ROC", "Small | 270mm h x 310mm w x 600mm l", "Rock", Decimal("809.21"), 0),
                ("CLETRCPOT-SM-VEL", "Small | 270mm h x 310mm w x 600mm l", "Velvet", Decimal("809.21"), 0),
            ]
        },
        {
            "name": "Cedric Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("CEDCPOT-SM-AMP", "Small", "Amper", Decimal("53.23"), 0),
                ("CEDCPOT-SM-FWH", "Small", "Flinted White", Decimal("53.23"), 0),
                ("CEDCPOT-SM-GRA", "Small", "Granite", Decimal("53.23"), 0),
                ("CEDCPOT-SM-GRA-2", "Small", "Granite Sealed", Decimal("53.23"), 0),
                ("CEDCPOT-SM-ROC", "Small", "Rock", Decimal("53.23"), 0),
                ("CEDCPOT-SM-VEL", "Small", "Velvet", Decimal("53.23"), 0),
            ]
        },
        {
            "name": "Carrington Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("CARCPOT-LG-AMP", "Large | 600mm x 590mm", "Amper", Decimal("2216.54"), 0),
                ("CARCPOT-LG-FWH", "Large | 600mm x 590mm", "Flinted White", Decimal("2216.54"), 0),
                ("CARCPOT-LG-GRA", "Large | 600mm x 590mm", "Granite", Decimal("2216.54"), 0),
                ("CARCPOT-LG-GRA-2", "Large | 600mm x 590mm", "Granite Sealed", Decimal("2216.54"), 0),
                ("CARCPOT-LG-ROC", "Large | 600mm x 590mm", "Rock", Decimal("2216.54"), 0),
                ("CARCPOT-LG-VEL", "Large | 600mm x 590mm", "Velvet", Decimal("2216.54"), 0),
            ]
        },
        {
            "name": "Carmen Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("CARCPOT-570-AMP", "570mm x 580mm", "Amper", Decimal("861.98"), 0),
                ("CARCPOT-570-FWH", "570mm x 580mm", "Flinted White", Decimal("861.98"), 0),
                ("CARCPOT-570-GRA", "570mm x 580mm", "Granite", Decimal("861.98"), 0),
                ("CARCPOT-570-GRA-2", "570mm x 580mm", "Granite Sealed", Decimal("861.98"), 0),
                ("CARCPOT-570-ROC", "570mm x 580mm", "Rock", Decimal("861.98"), 0),
                ("CARCPOT-570-VEL", "570mm x 580mm", "Velvet", Decimal("861.98"), 0),
            ]
        },
        {
            "name": "Bolivia Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("BOLCPOT-SM-AMP", "Small | 290MMX290MM", "amper", Decimal("402.37"), 0),
                ("BOLCPOT-SM-ANT", "Small | 290MMX290MM", "antique rust", Decimal("402.37"), 0),
                ("BOLCPOT-SM-BRO", "Small | 290MMX290MM", "bronze", Decimal("402.37"), 0),
                ("BOLCPOT-SM-CHR", "Small | 290MMX290MM", "charcoal", Decimal("402.37"), 0),
                ("BOLCPOT-SM-CHR-2", "Small | 290MMX290MM", "chryso black", Decimal("402.37"), 0),
                ("BOLCPOT-SM-GRA", "Small | 290MMX290MM", "granite", Decimal("402.37"), 0),
            ]
        },
        {
            "name": "Baobab Concrete Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("BOACPOT-LG-AMP", "Large | 800MM X 850MM", "Amper", Decimal("4098.80"), 0),
                ("BOACPOT-LG-FWH", "Large | 800MM X 850MM", "Flinted White", Decimal("4098.80"), 0),
                ("BOACPOT-LG-GRA", "Large | 800MM X 850MM", "Granite", Decimal("4098.80"), 0),
                ("BOACPOT-LG-GRA-2", "Large | 800MM X 850MM", "Granite Sealed", Decimal("4098.80"), 0),
                ("BOACPOT-LG-ROC", "Large | 800MM X 850MM", "Rock", Decimal("4098.80"), 0),
                ("BOACPOT-LG-VEL", "Large | 800MM X 850MM", "Velvet", Decimal("4098.80"), 0),
            ]
        },
        {
            "name": "Aztec Plant pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("AZTCPOT-LG-AMP", "Large | 1200mm x 420mm", "Amper", Decimal("2659.80"), 0),
                ("AZTCPOT-LG-FWH", "Large | 1200mm x 420mm", "Flinted White", Decimal("2659.80"), 0),
                ("AZTCPOT-LG-GRA", "Large | 1200mm x 420mm", "Granite", Decimal("2659.80"), 0),
                ("AZTCPOT-LG-GRA-2", "Large | 1200mm x 420mm", "Granite Sealed", Decimal("2659.80"), 0),
                ("AZTCPOT-LG-ROC", "Large | 1200mm x 420mm", "Rock", Decimal("2659.80"), 0),
                ("AZTCPOT-LG-VEL", "Large | 1200mm x 420mm", "Velvet", Decimal("2659.80"), 0),
            ]
        },
        {
            "name": "Rum Plant pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("RUMCPOT-SM-AMP", "Small", "Amper", Decimal("485.00"), 0),
                ("RUMCPOT-SM-GRD", "Small", "Granite dark", Decimal("485.00"), 0),
                ("RUMCPOT-SM-ROC", "Small", "Rock", Decimal("485.00"), 0),
                ("RUMCPOT-SM-VEL", "Small", "Velvet", Decimal("485.00"), 0),
                ("RUMCPOT-SM-CHR", "Small", "Chryso Black", Decimal("485.00"), 0),
                ("RUMCPOT-SM-ROL", "Small", "Rolled white", Decimal("485.00"), 0),
            ]
        },
        {
            "name": "Premium Arizona Plant pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("ARICPOT-SM-AMP", "Small | 720mm L x 530mm W x 510mm H", "Amper", Decimal("1326.40"), 0),
                ("ARICPOT-SM-FWH", "Small | 720mm L x 530mm W x 510mm H", "Flinted White", Decimal("1326.40"), 0),
                ("ARICPOT-SM-GRL", "Small | 720mm L x 530mm W x 510mm H", "Granite light", Decimal("1326.40"), 0),
                ("ARICPOT-SM-GRA", "Small | 720mm L x 530mm W x 510mm H", "Granite dark sealed", Decimal("1326.40"), 0),
                ("ARICPOT-SM-ROC", "Small | 720mm L x 530mm W x 510mm H", "Rock", Decimal("1326.40"), 0),
                ("ARICPOT-SM-VEL", "Small | 720mm L x 530mm W x 510mm H", "Velvet", Decimal("1326.40"), 0),
            ]
        },
        {
            "name": "Amazon Plant Pot",
            "description": "",
            "category": "Concrete Pot",
            "skus": [
                ("AMACPOT-LG-AMP", "Large | 1700mm x 600mm", "Amper", Decimal("4425.98"), 0),
                ("AMACPOT-LG-FWH", "Large | 1700mm x 600mm", "Flinted White", Decimal("4425.98"), 0),
                ("AMACPOT-LG-GRA", "Large | 1700mm x 600mm", "Granite", Decimal("4425.98"), 0),
                ("AMACPOT-LG-GRA-2", "Large | 1700mm x 600mm", "Granite Sealed", Decimal("4425.98"), 0),
                ("AMACPOT-LG-ROC", "Large | 1700mm x 600mm", "Rock", Decimal("4425.98"), 0),
                ("AMACPOT-LG-VEL", "Large | 1700mm x 600mm", "Velvet", Decimal("4425.98"), 0),
            ]
        },
    ]

    for prod_data in product_data:
        existing = db.query(Product).filter(Product.name == prod_data["name"]).first()
        if existing:
            print(f"Product already exists: {prod_data['name']}")
            products.append(existing)
            continue

        product = Product(
            name=prod_data["name"],
            description=prod_data["description"],
            category=prod_data["category"],
        )
        db.add(product)
        db.flush()

        for code, size, color, price, stock in prod_data["skus"]:
            sku = SKU(
                product_id=product.id,
                code=code,
                size=size,
                color=color,
                base_price_rands=price,
                stock_quantity=stock,
            )
            db.add(sku)
            print(f"  Created SKU: {code}")

        products.append(product)
        print(f"Created product: {prod_data['name']}")

    db.commit()
    return products


def main():
    db = SessionLocal()
    try:
        print("=== Seeding Garden Solutions Database ===\n")

        # Users
        print("--- Users ---")
        admin = seed_admin_user(db)
        users = seed_test_users(db)
        sales_user = users.get(UserRole.SALES)

        # Price tiers
        print("\n--- Price Tiers ---")
        tiers = seed_price_tiers(db)

        # Clients (created by admin per spec)
        print("\n--- Clients ---")
        clients = seed_clients(db, tiers, admin, sales_user)

        # Products and SKUs
        print("\n--- Products and SKUs ---")
        products = seed_products_and_skus(db)

        print("\n--- Sales Agents ---")
        sales_agent = db.query(SalesAgent).filter(SalesAgent.code == "4500").first()
        if not sales_agent:
            sales_agent = SalesAgent(name="Sue Elmira", code="4500", phone="082 4644 376", is_active=True)
            db.add(sales_agent)
            db.commit()
            print("Created sales agent: Sue Elmira (4500)")
        else:
            print("Sales agent already exists: 4500")

        print("\n--- Delivery Teams ---")
        team_defs = [
            ("D-4501", "Delivery Team Alpha", ["Aiden Driver", "Lea Runner", "Sam Loader"]),
            ("D-4502", "Delivery Team Bravo", ["Nia Driver", "Tariq Runner", "Olivia Loader"]),
            ("D-4503", "Delivery Team Charlie", ["Ben Driver", "Zara Runner", "Mila Loader"]),
        ]
        for code, team_name, member_names in team_defs:
            delivery_team = db.query(DeliveryTeam).filter(DeliveryTeam.code == code).first()
            if not delivery_team:
                delivery_team = DeliveryTeam(name=team_name, code=code, is_active=True)
                db.add(delivery_team)
                db.commit()
                print(f"Created delivery team: {code}")
            else:
                print(f"Delivery team already exists: {code}")

            for name in member_names:
                member = (
                    db.query(DeliveryTeamMember)
                    .filter(DeliveryTeamMember.delivery_team_id == delivery_team.id, DeliveryTeamMember.name == name)
                    .first()
                )
                if not member:
                    member = DeliveryTeamMember(delivery_team_id=delivery_team.id, name=name, is_active=True)
                    db.add(member)
                    print(f"  Created delivery team member: {name}")
            db.commit()

        print("\n--- Stores ---")
        store_data = [
            ("Pot and Planter - Church Street", "POT-JHB-CHURCH", "nursery"),
            ("Pot and Planter - Cornubia Mall", "POT-KZN-CORNUBIA", "nursery"),
            ("Pot and Planter - Table Bay Mall", "POT-CPT-TABLEBAY", "nursery"),
            ("Pot and Planter - Cedar", "POT-JHB-CEDAR", "nursery"),
            ("PotShack Online Store", "SHOP-ONLINE", "shopify"),
        ]
        for name, code, store_type in store_data:
            store = db.query(Store).filter(Store.code == code).first()
            if not store:
                store = Store(name=name, code=code, store_type=store_type, is_active=True)
                db.add(store)
                db.commit()
                print(f"Created store: {code}")
            else:
                print(f"Store already exists: {code}")

        print("\n=== Seeding complete! ===")
        print(f"\nCreated: {len(tiers)} price tiers, {len(clients)} clients, {len(products)} products")

    finally:
        db.close()


if __name__ == "__main__":
    main()
