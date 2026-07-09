from enum import Enum


class OrderStatus(str, Enum):
    TEMP = "TEMP"
    CLOSE = "CLOSE"


class SearchOp(str, Enum):
    LT = "<"
    GT = ">"
    EQ = "="


class Role(str, Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class StockResult(str, Enum):
    OK = "OK"
    INSUFFICIENT = "INSUFFICIENT"
    OUT_OF_STOCK = "OUT_OF_STOCK"
