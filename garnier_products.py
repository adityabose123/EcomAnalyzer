"""The Garnier products to analyse (names read off the supplied pack shots in garnier_images/)."""
import base64
from pathlib import Path

IMG_DIR = Path(__file__).parent / "garnier_images"

# key, display name, category (decides which competitor pool is searched), Amazon search query,
# words that must all appear in the Amazon listing title for it to count as this product, pack-shot file
PRODUCTS = [
    ("niacinamide-cream", "Garnier Niacinamide Fresh & Plump Oil-Free 48H Hydrating Cream", "moisturizer",
     "Garnier Niacinamide Fresh Plump 48H Hydrating Cream", ["niacinamide", "plump"], "niacinamide-fresh-plump-cream.png"),
    ("salicylic-cream", "Garnier Salicylic Fresh & Matte Oil-Free 48H Hydrating Cream", "moisturizer",
     "Garnier Salicylic Fresh Matte 48H Hydrating Cream", ["salicylic", "matte"], "salicylic-fresh-matte-cream.png"),
    ("vitamin-c-cream", "Garnier Vitamin C Fresh & Bright Oil-Free 48H Hydrating Cream", "moisturizer",
     "Garnier Vitamin C Fresh Bright 48H Hydrating Cream", ["vitamin c", "fresh"], "vitamin-c-fresh-bright-cream.webp"),
    ("vitamin-c-cleanser", "Garnier Bright Complete Vitamin C Serum Cleanser", "face wash",
     "Garnier Bright Complete Vitamin C Serum Cleanser", ["bright complete", "serum", "cleanser"], "bright-complete-vitamin-c-serum-cleanser.webp"),
    ("super-uv-sunscreen", "Garnier Super UV Cooling Watergel Sunscreen SPF 50+ with Vitamin C", "sunscreen",
     "Garnier Super UV Cooling Watergel Sunscreen SPF 50", ["super uv", "watergel"], "super-uv-cooling-watergel-sunscreen.webp"),
]
KEYS = [p[0] for p in PRODUCTS]


def as_dict(p):
    return dict(zip(["key", "name", "category", "query", "must", "image"], p))


def image_data_uri(filename):
    f = IMG_DIR / filename
    mime = "image/webp" if f.suffix == ".webp" else "image/png"
    return f"data:{mime};base64," + base64.b64encode(f.read_bytes()).decode()


def matches(title, must):
    t = (title or "").lower()
    return "garnier" in t and all(w in t for w in must)
