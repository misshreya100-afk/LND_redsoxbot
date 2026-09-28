from bot import build_tracking_message


def test_build_tracking_message_includes_order_id_and_status():
    order = {
        "id": 42,
        "status": "OUT_FOR_DELIVERY",
        "items": "Whiskey x2",
        "total": 120,
        "address": "Boston, MA",
    }

    text = build_tracking_message(order)

    assert "#42" in text
    assert "OUT_FOR_DELIVERY" in text
    assert "Boston, MA" in text
    assert "Whiskey x2" in text
