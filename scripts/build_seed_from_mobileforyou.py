"""One-time data prep: transform the mobileforyou catalog into our seed file.

Reads the source products.json (Hebrew/ILS store) and writes a self-contained
`data/products.seed.json` in our schema: English names/descriptions, USD prices.
The output is committed so the repo does not depend on mobileforyou at runtime.
"""
import json
import pathlib

SRC = r"C:/Users/Adir/Desktop/Coding/Dev/mobileforyou/data/products.json"
OUT = pathlib.Path(__file__).resolve().parents[1] / "data" / "products.seed.json"
ILS_TO_USD = 0.27  # ~1 USD = 3.7 ILS


def build_name(x: dict) -> str:
    storage = x.get("storage")
    name = f"{x['brand']} {x['model']}"
    if storage and storage not in ("N/A", "", None):
        name += f" {storage}"
    if x.get("condition") == "refurbished":
        name += " (Refurbished)"
    return name


def main() -> None:
    src = json.load(open(SRC, encoding="utf-8"))
    out, seen = [], set()
    for x in src:
        if not isinstance(x.get("price"), (int, float)):
            continue
        name = build_name(x)
        if name in seen:
            continue
        seen.add(name)
        desc = x.get("description_en") or (
            f"{name} — a {x.get('condition', 'new')} "
            f"{x.get('category', 'device')} by {x['brand']}."
        )
        out.append({
            "name": name,
            "description": desc,
            "category": x.get("category"),
            "brand": x.get("brand"),
            "price_usd": round(x["price"] * ILS_TO_USD, 2),
            "stock": int(x.get("stock", 0)),
            "image_url": x.get("image_url"),
            "specs": {
                "model": x.get("model"),
                "storage": x.get("storage"),
                "condition": x.get("condition"),
                "category": x.get("category"),
                "tags": x.get("tags", []),
                "is_best_seller": x.get("is_best_seller", False),
                "is_promotion": x.get("is_promotion", False),
            },
        })
    OUT.parent.mkdir(exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"wrote {len(out)} products to {OUT}")


if __name__ == "__main__":
    main()
