"""Turn a Product row into the text blob we embed.

Includes the descriptive fields a shopper would search by (name, brand, category,
description, key specs) plus a coarse stock marker. Note: the *embedding* is over
stable descriptive text — live stock is always re-read from MySQL at answer time,
so a stale marker here never misleads the shopper.
"""


def build_blob(product) -> str:
    parts = [product.name]
    if product.brand:
        parts.append(f"Brand: {product.brand}")
    if product.category:
        parts.append(f"Category: {product.category}")
    if product.description:
        parts.append(product.description)
    if product.specs:
        parts.append("Specs: " + ", ".join(
            f"{k}: {v}" for k, v in product.specs.items()))
    parts.append("In stock" if (product.stock or 0) > 0 else "Out of stock")
    return " | ".join(parts)
