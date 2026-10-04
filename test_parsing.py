import parsing as P

def test_size():
    assert P.parse_size("Garnier Moisturizer 50 ml") == (50, "ml")
    assert P.parse_size("Face wash 2 x 100 ml") == (200, "ml")
    assert P.parse_size("Cream 1 L") == (1000, "ml")
    assert P.parse_size("Shampoo 340ml (Pack of 2)") == (680, "ml")
    assert P.parse_size("Color Naturals 70 ml + 60 g") == (130, "ml")
    assert P.parse_size("Nothing here") == (None, None)

def test_nums():
    assert P.parse_price("₹1,299.00") == 1299.0
    assert P.parse_count("1.2K") == 1200 and P.parse_count("12,345 ratings") == 12345
    assert P.parse_rating("4.2 out of 5 stars") == 4.2

def test_category():
    assert P.infer_category("Garnier Bright Complete Vitamin C Face Wash") == "face wash"
    assert P.infer_category("Garnier Hair Colour Black Naturals") == "hair color"
    assert P.infer_category("Garnier Light Complete Serum Cream") == "face serum"

def test_spec_example():
    g = {"unit": "ml", "unit_price": 6.0, "ratings_count": 1000, "title": "Garnier X 50ml"}  # Rs300/50ml
    mk = lambda t, up, n, u="ml": {"title": t, "unit": u, "unit_price": up, "ratings_count": n}
    cands = [mk("A", 6.5, 5000), mk("B", 6.5, 500), mk("C", 12, 9000), mk("Garnier Y", 6, 9000), mk("D", 6, 9000, "g")]
    assert [c["title"] for c in P.select_competitors(g, cands, 20)] == ["A"]
