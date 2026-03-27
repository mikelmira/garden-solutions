"""
Seed script to create a rich, realistic demo dataset.

Usage:
    cd apps/api
    POSTGRES_PORT=5433 venv/bin/python -m scripts.seed_live_demo
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.user import UserRole
from app.models.price_tier import PriceTier
from app.models.sku import SKU
from app.models.order import OrderStatus
from app.schemas.order import OrderCreate, OrderItemCreate, OrderStatusUpdate
from app.schemas.delivery import DeliveryPartial, DeliveryComplete, DeliveryItemUpdate
from app.services.order import OrderService
from app.services.manufacturing import ManufacturingService
from app.services.delivery import DeliveryService
from scripts.seed_admin import seed_admin_user, seed_test_users, seed_price_tiers
from scripts._seed_helpers import (
    get_or_create_client,
    get_or_create_product_with_skus,
    get_order_by_note,
    get_sku_by_code,
    set_order_timestamps,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def seed_clients(db: Session, tiers: dict[str, PriceTier], admin_id, sales_id):
    clients = []
    client_data = [
        ("Pot & Planter (Pty) Ltd t/a The Pot Shack", "", "Tier A", admin_id),
        ("Adeo/Leroy Merlin South Africa (Pty) Ltd", "", "Tier B", admin_id),
        ("STODELS NURSERIES", "", "Tier B", sales_id),
        ("LIFESTYLE GARDEN CENTRE (PTY) LTD", "", "Tier C", admin_id),
        ("Starke Ayres (Rosebank)", "", "Tier B", sales_id),
        ("Burgess Landscapes Coastal (Pty) Ltd", "", "Tier C", sales_id),
        ("ECKARDS GARDEN PAVILION", "", "Tier A", sales_id),
        ("SAFARI GARDEN CENTRE", "", "Tier A", admin_id),
        ("Life Green Group t/a Life Indoors", "", "Tier B", admin_id),
        ("FYNBOS LANDSCAPES", "", "Tier C", sales_id),
        ("Bidvest ExecuFlora JHB", "", "Tier B", admin_id),
        ("LOTS OF POTS", "", "Tier A", sales_id),
        ("Greenery Guru", "", "Tier C", sales_id),
        ("Coenique Landscaping", "", "Tier C", sales_id),
        ("GARDENSHOP PARKTOWN", "", "Tier A", admin_id),
        ("AE NEL t/a PLANT PLEASURE", "", "Tier B", sales_id),
        ("Arlene Stone interiors", "", "Tier C", sales_id),
        ("B.T. Decor cc", "", "Tier C", sales_id),
        ("Bar Events", "", "Tier C", admin_id),
        ("BBR INVESTMENT HOLDING PTY LTD", "", "Tier B", admin_id),
        ("Blend Property 20 (Pty) Ltd", "", "Tier C", admin_id),
        ("BluePrint Business Corp", "", "Tier C", admin_id),
        ("Botanical Haven", "", "Tier B", sales_id),
        ("BROADACRES LANDSCAPES", "", "Tier C", sales_id),
        ("BUDS AND PETALS PTY LTD", "", "Tier B", admin_id),
        ("CONCRETE & GARDEN CREATIONS", "", "Tier C", sales_id),
        ("Create a Landscape", "", "Tier C", sales_id),
        ("Exclusive Landscapes", "", "Tier C", sales_id),
        ("Fourways Airconditioning Cape (PTY) Ltd", "", "Tier B", admin_id),
        ("Fresh Earth Gardens", "", "Tier C", sales_id),
        ("Garden Heart cc", "", "Tier B", admin_id),
        ("Garden Mechanix", "", "Tier C", sales_id),
        ("GARDEN VALE", "", "Tier B", admin_id),
        ("GOODIES FOR GARDENS KEMPTON PARK", "", "Tier A", admin_id),
        ("Hadland Business Pty Ltd t/a Working Hands", "", "Tier B", admin_id),
        ("Builders Warehouse Strubens Valley", "", "Tier A", admin_id),
        ("Builders Warehouse Centurion", "", "Tier A", admin_id),
        ("Builders Warehouse Rivonia", "", "Tier A", admin_id),
        ("Builders Express Southgate", "", "Tier A", admin_id),
        ("Builders Express Lynnwood", "", "Tier A", admin_id),
        ("Builders Express Wonderpark", "", "Tier A", admin_id),
        ("Builders Express Vredenburg", "", "Tier A", admin_id),
        ("Alan Maher", "", "Tier C", sales_id),
        ("Alicia Coetzee", "", "Tier C", sales_id),
        ("Alicia Lesch", "", "Tier C", sales_id),
        ("Allison Van Manen", "", "Tier C", sales_id),
        ("Bob Bhaga", "", "Tier C", sales_id),
        ("BRYAN", "", "Tier C", admin_id),
        ("C-Pac Co Packers", "", "Tier B", admin_id),
        ("Hadland Business Pty Ltd", "", "Tier B", admin_id),
    ]

    for name, address, tier_name, owner_id in client_data:
        client = get_or_create_client(
            db,
            name=name,
            tier_id=tiers[tier_name].id,
            created_by=owner_id,
            address=address,
        )
        clients.append(client)

    return clients


def seed_products(db: Session) -> list[SKU]:
    products = [
        (
            "Premium Bolivia Trough Plant Pot",
            "",
            "Concrete Pots",
            [
                ("PBOLTRPP-LG-AMP", "Large | 280mm x 325mm x 715mm", "Amper", Decimal("901.00"), 0, True),
                ("PBOLTRPP-LG-FWH", "Large | 280mm x 325mm x 715mm", "Flinted White", Decimal("901.00"), 0, True),
                ("PBOLTRPP-LG-ROC", "Large | 280mm x 325mm x 715mm", "Rock", Decimal("901.00"), 0, True),
            ],
        ),
        (
            "Premium Chunky Trough Plant Pot",
            "",
            "Concrete Pot",
            [
                ("PCHUTRPP-SM-AMP", "Small | 310mm X 300mm X 600mm", "Amper", Decimal("811.76"), 0, True),
                ("PCHUTRPP-SM-FWH", "Small | 310mm X 300mm X 600mm", "Flinted White", Decimal("811.76"), 0, True),
                ("PCHUTRPP-MD-AMP", "Medium | 340mm x 340mm x 800mm", "Amper", Decimal("1052.94"), 0, True),
            ],
        ),
        (
            "Amazon Plant Pot",
            "",
            "Concrete Pot",
            [
                ("AMACPOT-LG-AMP", "Large | 840mm X 500mm", "Amper", Decimal("1867.68"), 0, True),
                ("AMACPOT-LG-FWH", "Large | 840mm X 500mm", "Flinted White", Decimal("1867.68"), 0, True),
                ("AMACPOT-LG-GRA", "Large | 840mm X 500mm", "Granite", Decimal("1867.68"), 0, True),
            ],
        ),
        (
            "Baobab Concrete Pot",
            "",
            "Concrete Pot",
            [
                ("BOACPOT-LG-AMP", "Large | 560mm X 480mm", "Amper", Decimal("995.00"), 0, True),
                ("BOACPOT-LG-FWH", "Large | 560mm X 480mm", "Flinted White", Decimal("995.00"), 0, True),
                ("BOACPOT-LG-GRA", "Large | 560mm X 480mm", "Granite", Decimal("995.00"), 0, True),
            ],
        ),
        (
            "Premium Windsor Plant Pot",
            "",
            "Concrete Pot",
            [
                ("PWINPP-SM-AMP", "Small | 370mm x 240mm", "Amper", Decimal("449.91"), 0, True),
                ("PWINPP-SM-FWH", "Small | 370mm x 240mm", "Flinted White", Decimal("449.91"), 0, True),
                ("PWINPP-SM-GRA", "Small | 370mm x 240mm", "Granite", Decimal("449.91"), 0, True),
            ],
        ),
        (
            "Kathy Plant Pot",
            "",
            "Concrete Pot",
            [
                ("KATCPOT-LG-AMP", "Large | 530mm x 555mm", "Amper", Decimal("1052.13"), 0, True),
                ("KATCPOT-LG-FWH", "Large | 530mm x 555mm", "Flinted White", Decimal("1052.13"), 0, True),
                ("KATCPOT-LG-ROC", "Large | 530mm x 555mm", "Rock", Decimal("1052.13"), 0, True),
            ],
        ),
        (
            "Drip Tray",
            "",
            "Concrete Tray",
            [
                ("DRITY-LG-AMP", "Large | 600mm", "Amper", Decimal("197.06"), 0, True),
                ("DRITY-LG-FWH", "Large | 600mm", "Flinted White", Decimal("197.06"), 0, True),
                ("DRITY-LG-GRL", "Large | 600mm", "Granite Light", Decimal("197.06"), 0, True),
            ],
        ),
        (
            "Round Tray",
            "",
            "Concrete Tray",
            [
                ("ROUTY-SM-AMP", "Small | 380mm", "Amper", Decimal("118.76"), 0, True),
                ("ROUTY-SM-FWH", "Small | 380mm", "Flinted White", Decimal("118.76"), 0, True),
                ("ROUTY-SM-GRL", "Small | 380mm", "Granite Light", Decimal("118.76"), 0, True),
            ],
        ),
        (
            "Jessica Plant Pot",
            "",
            "Concrete Pot",
            [
                ("JESCPOT-600-AMP", "Jumbo | 600mm X 710mm", "Amper", Decimal("1566.36"), 0, True),
                ("JESCPOT-600-FWH", "Jumbo | 600mm X 710mm", "Flinted White", Decimal("1566.36"), 0, True),
                ("JESCPOT-600-ROC", "Jumbo | 600mm X 710mm", "Rock", Decimal("1566.36"), 0, True),
            ],
        ),
        (
            "Geni Concrete Pot",
            "",
            "Concrete Pot",
            [
                ("GENCPOT-XL-AMP", "Extra Large | 1300mm x 840mm", "amper", Decimal("4538.58"), 0, True),
                ("GENCPOT-XL-FWH", "Extra Large | 1300mm x 840mm", "flinted white", Decimal("4538.58"), 0, True),
                ("GENCPOT-XL-ROC", "Extra Large | 1300mm x 840mm", "rock", Decimal("4538.58"), 0, True),
            ],
        ),
    ]

    for name, desc, category, skus in products:
        get_or_create_product_with_skus(db, name, desc, category, skus)

    all_skus = db.query(SKU).all()
    return all_skus


def create_order(
    db: Session,
    order_service: OrderService,
    client_id,
    created_by,
    delivery_date: date,
    items: list[tuple[str, int]],
    note: str,
) -> int:
    existing = get_order_by_note(db, note)
    if existing:
        return existing.id

    order_items = []
    for code, qty in items:
        sku = get_sku_by_code(db, code)
        if not sku:
            raise ValueError(f"SKU not found for code: {code}")
        order_items.append(OrderItemCreate(sku_id=sku.id, quantity_ordered=qty))
    data = OrderCreate(client_id=client_id, items=order_items, delivery_date=delivery_date, notes=note)
    order = order_service.create_order(data, created_by)
    return order.id


def main():
    db = SessionLocal()
    try:
        print("=== Seeding Garden Solutions Live Demo ===\n")

        # Base seed (users + tiers)
        admin = seed_admin_user(db)
        users = seed_test_users(db)
        tiers = seed_price_tiers(db)
        sales_user = users[UserRole.SALES]
        mfg_user = users[UserRole.MANUFACTURING]
        delivery_user = users[UserRole.DELIVERY]

        # Clients
        clients = seed_clients(db, tiers, admin.id, sales_user.id)

        # Products + SKUs
        seed_products(db)

        order_service = OrderService(db)
        mfg_service = ManufacturingService(db)
        delivery_service = DeliveryService(db)

        today = date.today()
        created_base = datetime.now(timezone.utc) - timedelta(days=30)

        order_specs = [
            # note, client index, creator, delivery_date offset, items
            ("DEMO-ORDER-0001", 0, sales_user, -7, [("PBOLTRPP-LG-AMP", 12), ("PCHUTRPP-SM-AMP", 8)]),
            ("DEMO-ORDER-0002", 1, sales_user, 0, [("GENCPOT-XL-AMP", 3), ("PWINPP-SM-AMP", 10)]),
            ("DEMO-ORDER-0003", 2, admin, 3, [("KATCPOT-LG-AMP", 6), ("AMACPOT-LG-AMP", 4)]),
            ("DEMO-ORDER-0004", 3, admin, 7, [("PWINPP-SM-FWH", 15), ("BOACPOT-LG-AMP", 10)]),
            ("DEMO-ORDER-0005", 4, sales_user, 10, [("JESCPOT-600-AMP", 2), ("DRITY-LG-AMP", 5)]),
        ]

        print(f"Looping through {len(order_specs)} order specs...")
        created_orders = []
        for idx, (note, client_idx, creator, offset_days, items) in enumerate(order_specs, start=1):
            try:
                print(f"Creating order {note} for client idx {client_idx}...")
                order_id = create_order(
                    db,
                    order_service,
                    clients[client_idx].id,
                    creator,
                    today + timedelta(days=offset_days),
                    items,
                    note,
                )
                print(f"  -> Created order ID: {order_id}")
                order = get_order_by_note(db, note)
                created_at = created_base + timedelta(days=idx * 3)
                set_order_timestamps(db, order, created_at)
                created_orders.append(order)
            except Exception as e:
                print(f"  -> Errors creating order {note}: {e}")
        
        print(f"Total created orders: {len(created_orders)}")

        # Approve and progress orders
        # 1) Pending approval: DEMO-ORDER-0001 (leave pending)
        # 2) Approved, no manufacturing: DEMO-ORDER-0002
        # 3) Approved, partially manufactured: DEMO-ORDER-0003
        # 4) Fully manufactured, ready for delivery: DEMO-ORDER-0004
        # 5) Fully manufactured, delivery partial: DEMO-ORDER-0005
        # 6) Fully manufactured, completed delivery: DEMO-ORDER-0006
        # 7) Approved, no manufacturing: DEMO-ORDER-0007
        # 8) Fully manufactured, ready for delivery: DEMO-ORDER-0008
        # 9) Fully manufactured, ready for delivery: DEMO-ORDER-0009
        # 10) Approved, partially manufactured: DEMO-ORDER-0010

        status_update = OrderStatusUpdate(status=OrderStatus.APPROVED)

        def approve(order_note: str):
            order = get_order_by_note(db, order_note)
            if order and order.status == OrderStatus.PENDING_APPROVAL:
                order_service.update_order_status(order.id, status_update, admin)
            return order

        approve("DEMO-ORDER-0002")
        approve("DEMO-ORDER-0003")
        approve("DEMO-ORDER-0004")
        approve("DEMO-ORDER-0005")

        # Manufacturing updates
        def mfg(order_note: str, fraction: float):
            order = get_order_by_note(db, order_note)
            for item in order.items:
                target = int(item.quantity_ordered * fraction)
                if fraction >= 1.0:
                    target = item.quantity_ordered
                mfg_service.update_item_manufactured(item.id, target, mfg_user.id)

        mfg("DEMO-ORDER-0003", 0.5)
        mfg("DEMO-ORDER-0004", 1.0)
        mfg("DEMO-ORDER-0005", 1.0)

        # Partial delivery for DEMO-ORDER-0005
        order = get_order_by_note(db, "DEMO-ORDER-0005")
        if order and order.status in [OrderStatus.APPROVED, OrderStatus.READY_FOR_DELIVERY, OrderStatus.PARTIALLY_DELIVERED]:
            partial_items = []
            for item in order.items:
                partial_items.append(DeliveryItemUpdate(order_item_id=item.id, quantity_delivered=max(1, item.quantity_ordered // 2)))
            delivery_service.record_partial_delivery(
                order.id,
                DeliveryPartial(receiver_name="Receiving Desk", reason="Partial stock delivered", items=partial_items),
                performed_by=delivery_user.id,
            )

        # Set one order to ready_for_delivery status explicitly for funnel variety
        order = get_order_by_note(db, "DEMO-ORDER-0004")
        if order and order.status == OrderStatus.APPROVED:
            order.status = OrderStatus.READY_FOR_DELIVERY
            db.add(order)
            db.commit()

        print("\n=== Live demo seed complete ===")
    finally:
        db.close()


if __name__ == "__main__":
    main()
