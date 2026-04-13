from main import parse_products


def test_parse_products():
    result = parse_products(["candle:amber", "vase:cream white"])
    assert result == [
        {"name": "candle", "color": "amber"},
        {"name": "vase", "color": "cream white"},
    ]


def test_parse_products_no_color():
    result = parse_products(["candle"])
    assert result == [{"name": "candle", "color": "default"}]
