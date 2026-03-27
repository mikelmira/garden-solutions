"""
Product endpoints per docs:
- GET /api/v1/products (Protected)
- GET /api/v1/products/{id} (Protected, includes SKUs)
- POST /api/v1/products (Admin Only)
- POST /api/v1/products/{id}/skus (Admin Only)
"""
from uuid import UUID
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser, AdminUser
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductDetailResponse,
    ProductBulkImportRequest,
    SKUCreate,
    SKUUpdate,
    SKUResponse,
)
from app.schemas.common import DataResponse, ListResponse, PaginationMeta
from app.services.product import ProductService
from app.core.exceptions import ConflictException, NotFoundException
from app.models.product import Product

router = APIRouter()
UPLOAD_ROOT = Path(__file__).resolve().parent.parent.parent / "uploads" / "products"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.get("", response_model=ListResponse[ProductDetailResponse])
def list_products(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    category: str | None = Query(None),
):
    """
    List all products with their SKUs.
    """
    skip = (page - 1) * size
    service = ProductService(db)
    products, total = service.get_products(
        skip=skip,
        limit=size,
        is_active=is_active,
        category=category,
    )

    return ListResponse(
        data=[ProductDetailResponse.model_validate(p) for p in products],
        pagination=PaginationMeta(total=total, page=page, size=size),
    )


@router.get("/{product_id}", response_model=DataResponse[ProductDetailResponse])
def get_product(
    product_id: UUID,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Get a single product with its SKUs.
    """
    service = ProductService(db)
    product = service.get_product_by_id(product_id)

    return DataResponse(data=ProductDetailResponse.model_validate(product))


@router.post("", response_model=DataResponse[ProductResponse], status_code=201)
def create_product(
    data: ProductCreate,
    current_user: AdminUser,  # Admin only
    db: Session = Depends(get_db),
):
    """
    Create a new product (Admin only).
    """
    service = ProductService(db)
    product = service.create_product(data, current_user)

    return DataResponse(data=ProductResponse.model_validate(product))


@router.post("/{product_id}/skus", response_model=DataResponse[SKUResponse], status_code=201)
def create_sku(
    product_id: UUID,
    data: SKUCreate,
    current_user: AdminUser,  # Admin only
    db: Session = Depends(get_db),
):
    """
    Add a SKU variant to a product (Admin only).
    """
    service = ProductService(db)
    sku = service.create_sku(product_id, data, current_user)

    return DataResponse(data=SKUResponse.model_validate(sku))


@router.patch("/{product_id}", response_model=DataResponse[ProductResponse])
def update_product(
    product_id: UUID,
    data: ProductUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Update a product (Admin only). Soft delete via is_active=false.
    """
    service = ProductService(db)
    product = service.update_product(product_id, data, current_user)

    return DataResponse(data=ProductResponse.model_validate(product))


@router.patch("/{product_id}/skus/{sku_id}", response_model=DataResponse[SKUResponse])
def update_sku(
    product_id: UUID,
    sku_id: UUID,
    data: SKUUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Update a SKU (Admin only). Soft delete via is_active=false.
    """
    service = ProductService(db)
    sku = service.update_sku(product_id, sku_id, data, current_user)

    return DataResponse(data=SKUResponse.model_validate(sku))


@router.post("/import-csv", response_model=DataResponse[dict])
def import_products_csv(
    current_user: AdminUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Bulk import products and SKUs from CSV (Admin only).
    """
    content = file.file.read()
    service = ProductService(db)
    result = service.import_csv(content, current_user)
    return DataResponse(data=result)


@router.post("/bulk", response_model=ListResponse[ProductResponse])
def import_products_bulk(
    body: ProductBulkImportRequest,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Bulk upsert products and SKUs from JSON (Admin only).
    """
    service = ProductService(db)
    products = service.import_bulk(body, current_user)
    return ListResponse(
        data=[ProductResponse.model_validate(p) for p in products],
        pagination=PaginationMeta(total=len(products), page=1, size=len(products)),
    )


@router.post("/{product_id}/image", response_model=DataResponse[ProductResponse])
def upload_product_image(
    product_id: UUID,
    current_user: AdminUser,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload or replace a product image (Admin only).
    """
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise ConflictException("Unsupported image type")

    data = file.file.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise ConflictException("Image exceeds size limit")

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundException("Product not found")

    extension = Path(file.filename or "").suffix.lower()
    if not extension:
        extension = ".jpg" if file.content_type == "image/jpeg" else ".png"

    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    path = UPLOAD_ROOT / filename
    path.write_bytes(data)

    product.image_url = f"/uploads/products/{filename}"
    db.commit()
    db.refresh(product)
    return DataResponse(data=ProductResponse.model_validate(product))


@router.delete("/{product_id}/image", response_model=DataResponse[ProductResponse])
def delete_product_image(
    product_id: UUID,
    current_user: AdminUser,
    db: Session = Depends(get_db),
):
    """
    Remove a product image (Admin only).
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise NotFoundException("Product not found")

    if product.image_url and ("/uploads/products/" in product.image_url or "/static/products/" in product.image_url):
        filename = product.image_url.split("/products/")[-1]
        path = UPLOAD_ROOT / filename
        if path.exists():
            path.unlink()

    product.image_url = None
    db.commit()
    db.refresh(product)
    return DataResponse(data=ProductResponse.model_validate(product))
