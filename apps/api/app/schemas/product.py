"""
Product and SKU schemas.
Per docs: reject unknown fields (extra="forbid"), use specific types.
"""
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SKUBase(BaseModel):
    """Base SKU fields."""
    code: str = Field(min_length=1, max_length=50)
    size: str = Field(min_length=1, max_length=50)
    color: str = Field(min_length=1, max_length=50)
    base_price_rands: Decimal = Field(gt=Decimal("0"))
    stock_quantity: int = Field(ge=0, default=0)


class SKUCreate(SKUBase):
    """Schema for creating a SKU."""
    model_config = ConfigDict(extra="forbid")


class SKUUpdate(BaseModel):
    """Schema for updating a SKU."""
    model_config = ConfigDict(extra="forbid")

    code: str | None = Field(default=None, min_length=1, max_length=50)
    size: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, min_length=1, max_length=50)
    base_price_rands: Decimal | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class SKUResponse(SKUBase):
    """SKU response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_id: UUID
    is_active: bool


class ProductBase(BaseModel):
    """Base product fields."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = Field(default=None, max_length=500)


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    model_config = ConfigDict(extra="forbid")


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(default=None, max_length=100)
    image_url: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ProductResponse(ProductBase):
    """Product response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool


class ProductDetailResponse(ProductResponse):
    """Product detail response with nested SKUs."""
    skus: list[SKUResponse] = []


class ProductBulkSKU(BaseModel):
    """SKU payload for bulk product import."""
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=50)
    size: str = Field(min_length=1, max_length=50)
    color: str = Field(min_length=1, max_length=50)
    base_price_rands: Decimal = Field(gt=Decimal("0"))
    stock_quantity: int = Field(ge=0, default=0)
    is_active: bool | None = None


class ProductBulkItem(BaseModel):
    """Product payload for bulk import."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=255)
    category: str | None = Field(default=None, max_length=100)
    description_html: str | None = None
    image_url: str | None = Field(default=None, max_length=500)
    skus: list[ProductBulkSKU] = Field(min_length=1)


class ProductBulkImportRequest(BaseModel):
    """Bulk import request."""
    model_config = ConfigDict(extra="forbid")

    products: list[ProductBulkItem] = Field(min_length=1)
