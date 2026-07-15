"""Seed synthetic users + backdated order history into MySQL, so the churn
endpoint has realistic, varied people to score. Idempotent: clears prior
synthetic users first (identified by the is_synthetic flag). Not training data —
the model is trained separately on ml_training/data/churn_dataset.csv."""
import pathlib
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import numpy as np

# allow "import app" when run directly (host or container layout)
_here = pathlib.Path(__file__).resolve()
for _cand in (_here.parents[1] / "backend", _here.parents[1]):
    if (_cand / "app").is_dir():
        sys.path.insert(0, str(_cand))
        break

from app.core.database import SessionLocal  # noqa: E402
from app.core.enums import OrderStatus  # noqa: E402
from app.models import Favorite, Order, OrderItem, Product, User  # noqa: E402

N = 300
SEED = 42


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def seed_synthetic_users(db, n: int = N, seed: int = SEED) -> int:
    rng = np.random.default_rng(seed)
    products = db.query(Product).limit(60).all()
    if not products:
        print("no products found — run seed_products.py first")
        return 0

    # idempotent: remove prior synthetic users (cascades orders + favorites)
    db.query(User).filter(User.is_synthetic.is_(True)).delete(
        synchronize_session=False)
    db.commit()

    for i in range(n):
        churner = rng.random() < 0.4
        tenure = int(rng.integers(40, 700))
        user = User(username=f"synthetic_{i}", email=f"synthetic_{i}@demo.local",
                    password_hash="synthetic-no-login", is_synthetic=True,
                    created_at=_now() - timedelta(days=tenure))
        db.add(user)
        db.flush()

        n_orders = min(12, int(max(0, rng.poisson(1.5 if churner else 6))))
        recent_gap = int(rng.normal(120, 45) if churner else rng.normal(20, 15))
        recent_gap = max(1, min(recent_gap, tenure))

        for j in range(n_orders):
            # order j==0 anchors "recency" at recent_gap; others spread older
            gap = recent_gap if j == 0 else int(rng.integers(recent_gap, tenure + 1))
            when = _now() - timedelta(days=gap)
            product = products[int(rng.integers(0, len(products)))]
            qty = int(rng.integers(1, 3))
            order = Order(user_id=user.id, status=OrderStatus.CLOSE, is_temp=None,
                          total_price=Decimal(str(product.price_usd)) * qty,
                          created_at=when, closed_at=when)
            db.add(order)
            db.flush()
            db.add(OrderItem(order_id=order.id, product_id=product.id,
                             quantity=qty, unit_price=product.price_usd))

        n_fav = min(len(products), int(max(0, rng.poisson(1 if churner else 3))))
        for idx in rng.choice(len(products), size=n_fav, replace=False):
            db.add(Favorite(user_id=user.id, product_id=products[int(idx)].id))

    db.commit()
    return n


def main() -> None:
    db = SessionLocal()
    try:
        print("seeded", seed_synthetic_users(db), "synthetic users")
    finally:
        db.close()


if __name__ == "__main__":
    main()
