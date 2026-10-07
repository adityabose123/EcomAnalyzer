"""Synthetic DEMO data (clearly flagged) so the dashboard layout can be previewed without scraping.
Garnier names and pack shots are the real supplied ones; every price, rating and competitor is made up."""
import random
from datetime import datetime

import garnier_products as G


def product(asin, brand, title, price, qty, unit, rating, n, n_img, n_aplus, bullets, spec, desc, video=0):
    return {
        "asin": asin, "url": f"https://www.amazon.in/dp/{asin}", "title": title, "price": price, "size_qty": qty, "unit": unit,
        "unit_price": round(price / qty, 4), "rating": rating, "ratings_count": n,
        "above_fold": {"title": title, "brand": brand, "price_text": f"₹{price:g}", "discount": "-20%", "badges": ["Amazon's Choice"] if n > 20000 else [],
                       "bullets": bullets, "overview": {"Brand": brand, "Skin Type": "All"}, "video_count": video,
                       "images": ["x"] * n_img},
        "below_fold": {"aplus_images": ["x"] * n_aplus, "aplus_text": desc, "description": desc,
                       "spec_table": spec, "customers_say": "Customers like the texture and fragrance.", "rating_histogram": {"5": 60, "4": 20, "3": 10, "2": 5, "1": 5},
                       "reviews": [], "review_images": ["x"] * 3, "brand_story_images": [], "comparison_table": []},
    }


def build():
    rnd = random.Random(7)
    groups = []
    for i, p in enumerate(map(G.as_dict, G.PRODUCTS)):
        price, qty = rnd.choice([(199, 45), (299, 50), (349, 90)])
        g = product(f"DEMOG{i}", "Garnier", f"DEMO listing — {p['name']}, {qty} g", price, qty, "g", 4.1, 2500 + 300 * i, 7, 5,
                    ["Oil-free", "48H hydration", "4.5% actives"], {"Item Form": "Cream", "Net Quantity": f"{qty} g"}, "Garnier DEMO description.")
        g.update(category=p["category"], product_key=p["key"], product_name=p["name"], pack_image=G.image_data_uri(p["image"]))
        comps = []
        for j, brand in enumerate(["BrandA", "BrandB", "BrandC"]):
            cq = rnd.choice([30, 50, 100])
            cp = round(g["unit_price"] * rnd.uniform(0.85, 1.15) * cq)
            comps.append(product(f"DEMO{i}{j}", brand, f"DEMO {brand} {p['category'].title()} with Niacinamide, Hyaluronic, Dermatologist tested, {cq} ml",
                                 cp, cq, "ml", round(rnd.uniform(3.9, 4.5), 1), rnd.randint(5000, 40000), rnd.randint(5, 9), rnd.randint(0, 7),
                                 ["Niacinamide", "Hyaluronic acid", "Paraben free", "Clinically tested"][: rnd.randint(2, 4)],
                                 {"Item Form": "Gel", "Net Quantity": f"{cq} ml"}, f"{brand} " * rnd.randint(10, 60), rnd.randint(0, 1)))
        groups.append({"category": p["category"], "garnier": g, "competitors": comps})
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "marketplace": "amazon.in (DEMO — synthetic data)",
            "scrape_tolerance_pct": 40, "demo": True, "groups": groups}
