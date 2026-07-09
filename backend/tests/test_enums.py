from app.core.enums import OrderStatus, SearchOp, Role, StockResult


def test_order_status_values():
    assert OrderStatus.TEMP.value == "TEMP"
    assert OrderStatus.CLOSE.value == "CLOSE"


def test_search_op_maps_symbols():
    assert SearchOp("<") is SearchOp.LT
    assert SearchOp(">") is SearchOp.GT
    assert SearchOp("=") is SearchOp.EQ


def test_role_and_stock_result_exist():
    assert Role.CUSTOMER.value == "CUSTOMER"
    assert StockResult.OUT_OF_STOCK.value == "OUT_OF_STOCK"
