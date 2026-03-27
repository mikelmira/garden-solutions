"""Seed helpers for idempotent demo data creation."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.product import Product
from app.models.sku import SKU
from app.models.order import Order


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def get_client_by_name(db: Session, name: str) -> Client | None:
    return db.query(Client).filter(Client.name == name).first()


def get_or_create_client(
    db: Session,
    name: str,
    tier_id: UUID,
    created_by: UUID,
    address: str | None = None,
) -> Client:
    client = get_client_by_name(db, name)
    if client:
        updated = False
        if address and not client.address:
            client.address = address
            updated = True
        if client.created_by != created_by and not client.orders:
            client.created_by = created_by
            updated = True
        if updated:
            db.add(client)
            db.commit()
            db.refresh(client)
        return client

    client = Client(
        name=name,
        tier_id=tier_id,
        created_by=created_by,
        address=address,
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def get_product_by_name(db: Session, name: str) -> Product | None:
    return db.query(Product).filter(Product.name == name).first()


def get_sku_by_code(db: Session, code: str) -> SKU | None:
    return db.query(SKU).filter(SKU.code == code).first()


def get_or_create_product_with_skus(
    db: Session,
    name: str,
    description: str,
    category: str,
    skus: Iterable[tuple[str, str, str, Decimal, int, bool]],
) -> Product:
    product = get_product_by_name(db, name)
    if not product:
        product = Product(
            name=name,
            description=description,
            category=category,
            is_active=True,
        )
        db.add(product)
        db.flush()

    for code, size, color, price, stock, is_active in skus:
        sku = get_sku_by_code(db, code)
        if sku:
            updated = False
            if sku.product_id != product.id:
                sku.product_id = product.id
                updated = True
            if sku.is_active != is_active:
                sku.is_active = is_active
                updated = True
            if updated:
                db.add(sku)
            continue

        sku = SKU(
            product_id=product.id,
            code=code,
            size=size,
            color=color,
            base_price_rands=price,
            stock_quantity=stock,
            is_active=is_active,
        )
        db.add(sku)

    db.commit()
    db.refresh(product)
    return product


def get_order_by_note(db: Session, note: str) -> Order | None:
    return db.query(Order).filter(Order.notes == note).first()


def set_order_timestamps(db: Session, order: Order, created_at: datetime) -> None:
    order.created_at = created_at
    order.updated_at = created_at
    db.add(order)
    db.commit()
