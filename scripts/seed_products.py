"""Load data/products.seed.json into the database (idempotent by product name)."""
import json
import pathlib
import sys

# allow "import app" when run directly — find the dir that holds the app package
# (host layout: repo-root/backend/app ; container layout: /app/app)
_here = pathlib.Path(__file__).resolve()
for _cand in (_here.parents[1] / "backend", _here.parents[1]):
    if (_cand / "app").is_dir():
        sys.path.insert(0, str(_cand))
        break

from app.core.database import SessionLocal  # noqa: E402
from app.models import Product  # noqa: E402
from app.repositories.product_repository import ProductRepository  # noqa: E402

SEED = pathlib.Path(__file__).resolve().parents[1] / "data" / "products.seed.json"


def seed_products(db, items: list[dict]) -> int:
    repo = ProductRepository(db)
    for it in items:
        existing = repo.get_by_name(it["name"])
        if existing:
            existing.stock = it["stock"]
            existing.price_usd = it["price_usd"]
            existing.description = it.get("description")
            existing.image_url = it.get("image_url")
            existing.specs = it.get("specs")
        else:
            db.add(Product(
                name=it["name"],
                description=it.get("description"),
                category=it.get("category"),
                brand=it.get("brand"),
                price_usd=it["price_usd"],
                stock=it["stock"],
                image_url=it.get("image_url"),
                specs=it.get("specs"),
            ))
    db.commit()
    return len(items)


def main() -> None:
    items = json.load(open(SEED, encoding="utf-8"))
    db = SessionLocal()
    try:
        print("seeded", seed_products(db, items), "products")
    finally:
        db.close()


if __name__ == "__main__":
    main()
