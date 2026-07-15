"""Redis Stack vector store (VSS).

Products are embedded once and stored in a Redis hash keyed `product:vec:{id}`, and
an FT index (`FLOAT32[1536]`, COSINE, exact FLAT KNN) answers nearest-neighbour
queries. FLAT gives *exact* results — at ~151 products that's ideal; swapping "FLAT"
for "HNSW" is the one-line change to trade exactness for scale.
"""
import numpy as np
from redis.commands.search.field import NumericField, TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query

DIM = 1536  # text-embedding-3-small


def _to_bytes(vector) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


class VectorStore:
    INDEX = "idx:products"
    PREFIX = "product:vec:"

    def __init__(self, redis):
        self.r = redis

    def ensure_index(self) -> None:
        try:
            self.r.ft(self.INDEX).info()
            return  # already exists
        except Exception:
            pass
        schema = (
            VectorField("embedding", "FLAT",
                        {"TYPE": "FLOAT32", "DIM": DIM, "DISTANCE_METRIC": "COSINE"}),
            NumericField("product_id"),
            TextField("name"),
        )
        definition = IndexDefinition(prefix=[self.PREFIX], index_type=IndexType.HASH)
        self.r.ft(self.INDEX).create_index(schema, definition=definition)

    def is_empty(self) -> bool:
        try:
            return int(self.r.ft(self.INDEX).info()["num_docs"]) == 0
        except Exception:
            return True

    def upsert(self, product_id: int, vector, name: str) -> None:
        self.r.hset(f"{self.PREFIX}{product_id}", mapping={
            "product_id": product_id,
            "name": name,
            "embedding": _to_bytes(vector),
        })

    def knn(self, query_vector, k: int, exclude_id: int | None = None) -> list[int]:
        n = k + (1 if exclude_id is not None else 0)
        q = (Query(f"*=>[KNN {n} @embedding $vec AS score]")
             .sort_by("score")
             .return_fields("product_id", "score")
             .dialect(2))
        res = self.r.ft(self.INDEX).search(
            q, query_params={"vec": _to_bytes(query_vector)})
        ids = [int(doc.product_id) for doc in res.docs]
        if exclude_id is not None:
            ids = [i for i in ids if i != exclude_id]
        return ids[:k]

    def clear(self) -> None:
        for key in self.r.scan_iter(f"{self.PREFIX}*"):
            self.r.delete(key)
