"""
Product and SKU service.

Per docs:
- Products are accessible to all authenticated users
- Admin can create products and SKUs
"""
from uuid import UUID
import csv
from io import StringIO
from decimal import Decimal, InvalidOperation
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models.product import Product
from app.models.sku import SKU
from app.models.user import User
from app.schemas.product import ProductCreate, SKUCreate, ProductUpdate, SKUUpdate, ProductBulkImportRequest
from app.services.audit import AuditService
from app.models.audit_log import AuditAction
from app.core.exceptions import NotFoundException, ConflictException


class ProductService:
    """Service for product and SKU operations."""

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def get_products(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: bool | None = True,
        category: str | None = None,
    ) -> tuple[list[Product], int]:
        """
        Get all products with optional filtering.
        """
        query = self.db.query(Product)

        if is_active is not None:
            query = query.filter(Product.is_active == is_active)

        if category:
            query = query.filter(Product.category == category)

        total = query.count()
        products = query.offset(skip).limit(limit).all()

        return products, total

    def get_product_by_id(self, product_id: UUID) -> Product:
        """
        Get a single product by ID with its SKUs.
        """
        product = self.db.query(Product).filter(Product.id == product_id).first()

        if not product:
            raise NotFoundException(f"Product with id {product_id} not found")

        return product

    def create_product(self, data: ProductCreate, current_user: User) -> Product:
        """
        Create a new product (admin only enforced at router level).
        """
        product = Product(
            name=data.name,
            description=data.description,
            category=data.category,
            image_url=data.image_url,
        )
        self.db.add(product)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="product",
            entity_id=product.id,
            performed_by=current_user.id,
            payload={"name": data.name, "category": data.category},
        )

        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product_id: UUID, data: ProductUpdate, current_user: User) -> Product:
        """
        Update a product (admin only).
        """
        product = self.get_product_by_id(product_id)
        updates = {}

        if data.name is not None:
            product.name = data.name
            updates["name"] = data.name
        if data.description is not None:
            product.description = data.description
            updates["description"] = data.description
        if data.category is not None:
            product.category = data.category
            updates["category"] = data.category
        if data.image_url is not None:
            product.image_url = data.image_url
            updates["image_url"] = data.image_url
        if data.is_active is not None:
            product.is_active = data.is_active
            updates["is_active"] = data.is_active

        if updates:
            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="product",
                entity_id=product.id,
                performed_by=current_user.id,
                payload=updates,
            )

        self.db.commit()
        self.db.refresh(product)
        return product

    def create_sku(
        self, product_id: UUID, data: SKUCreate, current_user: User
    ) -> SKU:
        """
        Create a new SKU for a product (admin only).
        """
        # Verify product exists
        product = self.get_product_by_id(product_id)

        sku = SKU(
            product_id=product.id,
            code=data.code,
            size=data.size,
            color=data.color,
            base_price_rands=data.base_price_rands,
            stock_quantity=data.stock_quantity,
        )
        self.db.add(sku)
        self.db.flush()

        self.audit_service.log(
            action=AuditAction.CREATE,
            entity_type="sku",
            entity_id=sku.id,
            performed_by=current_user.id,
            payload={
                "code": data.code,
                "product_id": str(product_id),
                "base_price_rands": str(data.base_price_rands),
            },
        )

        self.db.commit()
        self.db.refresh(sku)
        return sku

    def update_sku(
        self, product_id: UUID, sku_id: UUID, data: SKUUpdate, current_user: User
    ) -> SKU:
        """
        Update a SKU (admin only).
        """
        sku = self.get_sku_by_id(sku_id)
        if str(sku.product_id) != str(product_id):
            raise NotFoundException(f"SKU with id {sku_id} not found for product {product_id}")

        updates = {}
        if data.code is not None:
            existing = self.db.query(SKU).filter(SKU.code == data.code, SKU.id != sku_id).first()
            if existing:
                raise ConflictException("SKU code already exists")
            sku.code = data.code
            updates["code"] = data.code
        if data.size is not None:
            sku.size = data.size
            updates["size"] = data.size
        if data.color is not None:
            sku.color = data.color
            updates["color"] = data.color
        if data.base_price_rands is not None:
            sku.base_price_rands = data.base_price_rands
            updates["base_price_rands"] = str(data.base_price_rands)
        if data.stock_quantity is not None:
            sku.stock_quantity = data.stock_quantity
            updates["stock_quantity"] = data.stock_quantity
        if data.is_active is not None:
            sku.is_active = data.is_active
            updates["is_active"] = data.is_active

        if updates:
            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="sku",
                entity_id=sku.id,
                performed_by=current_user.id,
                payload=updates,
            )

        self.db.commit()
        self.db.refresh(sku)
        return sku

    def update_sku_by_id(self, sku_id: UUID, data: SKUUpdate, current_user: User) -> SKU:
        """
        Update a SKU by ID (admin only).
        """
        sku = self.get_sku_by_id(sku_id)
        updates = {}

        if data.code is not None:
            existing = self.db.query(SKU).filter(SKU.code == data.code, SKU.id != sku_id).first()
            if existing:
                raise ConflictException("SKU code already exists")
            sku.code = data.code
            updates["code"] = data.code
        if data.size is not None:
            sku.size = data.size
            updates["size"] = data.size
        if data.color is not None:
            sku.color = data.color
            updates["color"] = data.color
        if data.base_price_rands is not None:
            sku.base_price_rands = data.base_price_rands
            updates["base_price_rands"] = str(data.base_price_rands)
        if data.stock_quantity is not None:
            sku.stock_quantity = data.stock_quantity
            updates["stock_quantity"] = data.stock_quantity
        if data.is_active is not None:
            sku.is_active = data.is_active
            updates["is_active"] = data.is_active

        if updates:
            self.audit_service.log(
                action=AuditAction.UPDATE,
                entity_type="sku",
                entity_id=sku.id,
                performed_by=current_user.id,
                payload=updates,
            )

        self.db.commit()
        self.db.refresh(sku)
        return sku

    def get_sku_by_id(self, sku_id: UUID) -> SKU:
        """
        Get a single SKU by ID.
        """
        sku = self.db.query(SKU).filter(SKU.id == sku_id).first()

        if not sku:
            raise NotFoundException(f"SKU with id {sku_id} not found")

        return sku

    def import_csv(self, content: bytes, current_user: User) -> dict:
        """
        Import products and SKUs from CSV content.
        Best-effort per row; failures do not halt the import.
        """
        text = content.decode("utf-8")
        reader = csv.DictReader(StringIO(text))

        created_products: set[UUID] = set()
        updated_products: set[UUID] = set()
        created_skus: set[UUID] = set()
        updated_skus: set[UUID] = set()
        failures: list[dict] = []

        def parse_bool(value: str | None) -> bool | None:
            if value is None:
                return None
            v = value.strip().lower()
            if v == "":
                return None
            if v in ("true", "1", "yes", "y"):
                return True
            if v in ("false", "0", "no", "n"):
                return False
            return None

        row_number = 1
        for row in reader:
            row_number += 1
            try:
                product_name = (row.get("product_name") or "").strip()
                sku_code = (row.get("sku_code") or "").strip()

                if not product_name:
                    raise ConflictException("product_name is required")
                if not sku_code:
                    raise ConflictException("sku_code is required")

                product_description = (row.get("product_description") or "").strip() or None
                product_category = (row.get("product_category") or "").strip() or None
                product_is_active = parse_bool(row.get("product_is_active"))

                sku_size = (row.get("sku_size") or "").strip() or None
                sku_color = (row.get("sku_color") or "").strip() or None
                sku_is_active = parse_bool(row.get("sku_is_active"))
                sku_stock_raw = (row.get("sku_stock_quantity") or "").strip()
                sku_price_raw = (row.get("sku_base_price_rands") or "").strip()

                sku_stock_quantity = None
                if sku_stock_raw != "":
                    sku_stock_quantity = int(sku_stock_raw)

                sku_base_price_rands = None
                if sku_price_raw != "":
                    sku_base_price_rands = Decimal(sku_price_raw)

                normalized_name = product_name.strip().lower()
                product = (
                    self.db.query(Product)
                    .filter(func.lower(func.trim(Product.name)) == normalized_name)
                    .first()
                )

                if not product:
                    product = Product(
                        name=product_name,
                        description=product_description,
                        category=product_category,
                        is_active=True if product_is_active is None else product_is_active,
                    )
                    self.db.add(product)
                    self.db.flush()
                    created_products.add(product.id)
                    self.audit_service.log(
                        action=AuditAction.CREATE,
                        entity_type="product",
                        entity_id=product.id,
                        performed_by=current_user.id,
                        payload={"name": product.name, "category": product.category},
                    )
                else:
                    updates = {}
                    if product_description is not None:
                        product.description = product_description
                        updates["description"] = product_description
                    if product_category is not None:
                        product.category = product_category
                        updates["category"] = product_category
                    if product_is_active is not None:
                        product.is_active = product_is_active
                        updates["is_active"] = product_is_active
                    if updates:
                        updated_products.add(product.id)
                        self.audit_service.log(
                            action=AuditAction.UPDATE,
                            entity_type="product",
                            entity_id=product.id,
                            performed_by=current_user.id,
                            payload=updates,
                        )

                sku = self.db.query(SKU).filter(SKU.code == sku_code).first()
                if sku:
                    if sku.product_id != product.id:
                        raise ConflictException("sku_code belongs to a different product")

                    updates = {}
                    if sku_size is not None:
                        sku.size = sku_size
                        updates["size"] = sku_size
                    if sku_color is not None:
                        sku.color = sku_color
                        updates["color"] = sku_color
                    if sku_base_price_rands is not None:
                        sku.base_price_rands = sku_base_price_rands
                        updates["base_price_rands"] = str(sku_base_price_rands)
                    if sku_stock_quantity is not None:
                        sku.stock_quantity = sku_stock_quantity
                        updates["stock_quantity"] = sku_stock_quantity
                    if sku_is_active is not None:
                        sku.is_active = sku_is_active
                        updates["is_active"] = sku_is_active

                    if updates:
                        updated_skus.add(sku.id)
                        self.audit_service.log(
                            action=AuditAction.UPDATE,
                            entity_type="sku",
                            entity_id=sku.id,
                            performed_by=current_user.id,
                            payload=updates,
                        )
                else:
                    if sku_size is None or sku_color is None or sku_base_price_rands is None:
                        raise ConflictException("sku_size, sku_color, sku_base_price_rands are required for new SKUs")
                    sku = SKU(
                        product_id=product.id,
                        code=sku_code,
                        size=sku_size,
                        color=sku_color,
                        base_price_rands=sku_base_price_rands,
                        stock_quantity=sku_stock_quantity or 0,
                        is_active=True if sku_is_active is None else sku_is_active,
                    )
                    self.db.add(sku)
                    self.db.flush()
                    created_skus.add(sku.id)
                    self.audit_service.log(
                        action=AuditAction.CREATE,
                        entity_type="sku",
                        entity_id=sku.id,
                        performed_by=current_user.id,
                        payload={"code": sku.code, "product_id": str(product.id)},
                    )

                self.db.commit()
            except (ValueError, InvalidOperation):
                self.db.rollback()
                failures.append(
                    {"row_number": row_number, "sku_code": row.get("sku_code"), "reason": "invalid numeric value"}
                )
            except Exception as exc:
                self.db.rollback()
                failures.append(
                    {"row_number": row_number, "sku_code": row.get("sku_code"), "reason": str(exc)}
                )

        return {
            "created_products": len(created_products),
            "updated_products": len(updated_products),
            "created_skus": len(created_skus),
            "updated_skus": len(updated_skus),
            "failures": failures,
        }

    def import_bulk(self, data: ProductBulkImportRequest, current_user: User) -> list[Product]:
        """
        Bulk upsert products and SKUs from JSON.
        Upsert by product name (case-insensitive trim) and SKU code (global).
        """
        seen_product_names: set[str] = set()
        seen_sku_codes: set[str] = set()

        for product in data.products:
            normalized = product.name.strip().lower()
            if normalized in seen_product_names:
                raise ConflictException(f"Duplicate product_name in payload: {product.name}")
            seen_product_names.add(normalized)
            for sku in product.skus:
                if sku.code in seen_sku_codes:
                    raise ConflictException(f"Duplicate sku_code in payload: {sku.code}")
                seen_sku_codes.add(sku.code)

        updated_products: list[Product] = []

        try:
            for product_data in data.products:
                normalized = product_data.name.strip().lower()
                product = (
                    self.db.query(Product)
                    .filter(func.lower(func.trim(Product.name)) == normalized)
                    .first()
                )

                if not product:
                    product = Product(
                        name=product_data.name,
                        description=product_data.description_html,
                        category=product_data.category,
                        image_url=product_data.image_url,
                        is_active=True,
                    )
                    self.db.add(product)
                    self.db.flush()
                    self.audit_service.log(
                        action=AuditAction.CREATE,
                        entity_type="product",
                        entity_id=product.id,
                        performed_by=current_user.id,
                        payload={"name": product.name, "category": product.category},
                    )
                else:
                    updates = {}
                    if product_data.description_html is not None:
                        product.description = product_data.description_html
                        updates["description"] = product_data.description_html
                    if product_data.category is not None:
                        product.category = product_data.category
                        updates["category"] = product_data.category
                    if product_data.image_url is not None:
                        product.image_url = product_data.image_url
                        updates["image_url"] = product_data.image_url
                    if updates:
                        self.audit_service.log(
                            action=AuditAction.UPDATE,
                            entity_type="product",
                            entity_id=product.id,
                            performed_by=current_user.id,
                            payload=updates,
                        )

                for sku_data in product_data.skus:
                    sku = self.db.query(SKU).filter(SKU.code == sku_data.code).first()
                    if sku:
                        if sku.product_id != product.id:
                            raise ConflictException(f"SKU code {sku_data.code} belongs to another product")
                        sku.size = sku_data.size
                        sku.color = sku_data.color
                        sku.base_price_rands = sku_data.base_price_rands
                        sku.stock_quantity = sku_data.stock_quantity
                        if sku_data.is_active is not None:
                            sku.is_active = sku_data.is_active

                        self.audit_service.log(
                            action=AuditAction.UPDATE,
                            entity_type="sku",
                            entity_id=sku.id,
                            performed_by=current_user.id,
                            payload={
                                "code": sku.code,
                                "size": sku.size,
                                "color": sku.color,
                                "base_price_rands": str(sku.base_price_rands),
                                "stock_quantity": sku.stock_quantity,
                                "is_active": sku.is_active,
                            },
                        )
                    else:
                        sku = SKU(
                            product_id=product.id,
                            code=sku_data.code,
                            size=sku_data.size,
                            color=sku_data.color,
                            base_price_rands=sku_data.base_price_rands,
                            stock_quantity=sku_data.stock_quantity,
                            is_active=True if sku_data.is_active is None else sku_data.is_active,
                        )
                        self.db.add(sku)
                        self.db.flush()
                        self.audit_service.log(
                            action=AuditAction.CREATE,
                            entity_type="sku",
                            entity_id=sku.id,
                            performed_by=current_user.id,
                            payload={"code": sku.code, "product_id": str(product.id)},
                        )

                updated_products.append(product)

            self.db.commit()
            for product in updated_products:
                self.db.refresh(product)
            return updated_products
        except Exception:
            self.db.rollback()
            raise
