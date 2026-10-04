"""Pure helpers: price / size / ratings parsing, category inference, competitor filtering."""
import re

# Ordered most-specific first. (category, search query, title keywords)
CATEGORIES = [
    ("hair color", "hair colour", ["hair colour", "hair color", "color naturals", "color sensational", "black naturals", "colour naturals"]),
    ("sheet mask", "sheet mask", ["sheet mask", "serum mask", "tissue mask"]),
    ("hair mask", "hair mask", ["hair mask", "hair masque"]),
    ("hair serum", "hair serum", ["hair serum"]),
    ("hair oil", "hair oil", ["hair oil"]),
    ("conditioner", "conditioner", ["conditioner"]),
    ("shampoo", "shampoo", ["shampoo"]),
    ("micellar water", "micellar water", ["micellar"]),
    ("cleanser", "face cleanser", ["cleanser", "cleansing"]),
    ("face wash", "face wash", ["face wash", "facewash", "foaming wash", "cleansing gel"]),
    ("face scrub", "face scrub", ["scrub", "exfoliat"]),
    ("sunscreen", "sunscreen", ["sunscreen", "sun screen", "spf", "uv "]),
    ("eye cream", "eye cream", ["eye cream", "eye gel", "eye roll"]),
    ("face serum", "face serum", ["serum"]),
    ("toner", "face toner", ["toner"]),
    ("lip balm", "lip balm", ["lip balm"]),
    ("body lotion", "body lotion", ["body lotion", "body milk", "body cream"]),
    ("moisturizer", "moisturizer", ["moisturizer", "moisturiser", "moisturizing", "cream", "gel", "lotion", "hydrat"]),
]

_UNIT = {"ml": "ml", "l": "ml", "ltr": "ml", "litre": "ml", "liter": "ml",
         "g": "g", "gm": "g", "gms": "g", "gram": "g", "grams": "g", "kg": "g"}
_MULT = {"l": 1000, "ltr": 1000, "litre": 1000, "liter": 1000, "kg": 1000}
_QTY = re.compile(r"(\d+(?:\.\d+)?)\s*(ml|ltr|litre|liter|l|gms|gm|grams|gram|g|kg)\b", re.I)
_MULTIPLY = re.compile(r"(\d+)\s*[x×]\s*(\d+(?:\.\d+)?)\s*(ml|ltr|litre|liter|l|gms|gm|grams|gram|g|kg)\b", re.I)
_PACK = re.compile(r"(?:pack\s*of|set\s*of|combo\s*of)\s*(\d+)|\b(\d+)\s*(?:pack|pcs|pieces)\b", re.I)


def parse_price(text):
    if not text:
        return None
    m = re.search(r"[\d,]+(?:\.\d+)?", text.replace("\u20b9", " "))
    return float(m.group(0).replace(",", "")) if m else None


def parse_count(text):
    """'12,345' -> 12345, '1.2K' -> 1200, '3.4M' -> 3400000."""
    if not text:
        return None
    m = re.search(r"([\d,.]+)\s*([KkMm]?)", text)
    if not m:
        return None
    try:
        n = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return int(n * {"k": 1_000, "m": 1_000_000}.get(m.group(2).lower(), 1))


def parse_rating(text):
    m = re.search(r"(\d(?:\.\d)?)\s*out of", text or "")
    return float(m.group(1)) if m else None


def parse_size(title):
    """Return (quantity, unit) normalised to ml or g, or (None, None).

    '50 ml' -> (50,'ml'); '2 x 50 ml' / 'pack of 2, 50ml' -> (100,'ml');
    '70 ml + 60 g' (hair colour kits) -> (130,'g'-ish: first unit wins).
    """
    if not title:
        return None, None
    m = _MULTIPLY.search(title)
    if m:
        n, q, u = int(m.group(1)), float(m.group(2)), m.group(3).lower()
        return n * q * _MULT.get(u, 1), _UNIT[u]
    found = _QTY.findall(title)
    if not found:
        return None, None
    unit = _UNIT[found[0][1].lower()]
    qtys = [float(q) * _MULT.get(u.lower(), 1) for q, u in found[:2] if _UNIT[u.lower()] == unit or "+" in title]
    # kits like "70 ml + 60 g" are summed; otherwise only the first quantity counts
    total = sum(qtys) if "+" in title and len(qtys) > 1 else qtys[0]
    pm = _PACK.search(title)
    if pm:
        total *= int(pm.group(1) or pm.group(2))
    return total, unit


def infer_category(title):
    t = (title or "").lower() + " "
    for name, _query, kws in CATEGORIES:
        if any(k in t for k in kws):
            return name
    return None


def category_query(name):
    for n, q, _ in CATEGORIES:
        if n == name:
            return q
    return name


def unit_price(price, qty):
    return round(price / qty, 4) if price and qty else None


def is_garnier(title):
    return "garnier" in (title or "").lower()


def select_competitors(garnier, candidates, tolerance_pct):
    """Brief rules: non-Garnier, same unit, price/unit within +-tolerance,
    and strictly more ratings than the Garnier product. Sorted by ratings desc."""
    gp, gr = garnier.get("unit_price"), garnier.get("ratings_count") or 0
    if not gp:
        return []
    out = []
    for c in candidates:
        if is_garnier(c.get("title")) or c.get("unit") != garnier.get("unit"):
            continue
        cp = c.get("unit_price")
        if not cp or abs(cp - gp) / gp * 100 > tolerance_pct:
            continue
        if (c.get("ratings_count") or 0) <= gr:
            continue
        out.append(c)
    return sorted(out, key=lambda c: c["ratings_count"], reverse=True)
