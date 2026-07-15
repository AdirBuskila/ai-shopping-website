from decimal import Decimal

from app.ai.product_text import build_blob
from app.models import Product


def test_blob_includes_name_brand_specs_and_stock():
    p = Product(name="Apple iPhone 13", brand="Apple", category="smartphone",
                description="A great phone", price_usd=Decimal("499"), stock=0,
                specs={"storage": "128GB"})
    blob = build_blob(p)
    assert "Apple iPhone 13" in blob
    assert "Apple" in blob
    assert "smartphone" in blob
    assert "storage" in blob and "128GB" in blob
    assert "Out of stock" in blob


def test_blob_marks_in_stock():
    p = Product(name="Google Pixel 8", price_usd=Decimal("301"), stock=5)
    assert "In stock" in build_blob(p)
