"""Embed the whole catalog into the Redis vector store (idempotent upsert)."""
from app.ai.embeddings import embed_many
from app.ai.product_text import build_blob
from app.repositories.product_repository import ProductRepository


def build_index(db, store, embed_many_fn=embed_many) -> int:
    products = ProductRepository(db).list_all()
    store.ensure_index()
    vectors = embed_many_fn([build_blob(p) for p in products])
    for product, vector in zip(products, vectors):
        store.upsert(product.id, vector, product.name)
    return len(products)
