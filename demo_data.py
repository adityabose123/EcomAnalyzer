"""Synthetic DEMO data (clearly flagged) so the dashboard layout can be previewed without scraping."""
import base64, random
from datetime import datetime


def ph(label, color):
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='600' height='600'><rect width='600' height='600' fill='{color}'/>"
           f"<text x='300' y='310' font-family='sans-serif' font-size='34' fill='white' text-anchor='middle'>{label}</text></svg>")
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def product(asin, brand, title, price, qty, unit, rating, n, color, n_img, n_aplus, bullets, spec, desc, video=0):
    return {
        "asin": asin, "url": f"https://www.amazon.in/dp/{asin}", "title": title, "price": price, "size_qty": qty, "unit": unit,
        "unit_price": round(price / qty, 4), "rating": rating, "ratings_count": n,
        "above_fold": {"title": title, "brand": brand, "price_text": f"₹{price:g}", "discount": "-20%", "badges": ["Amazon's Choice"] if n > 20000 else [],
                       "bullets": bullets, "overview": {"Brand": brand, "Skin Type": "All"}, "video_count": video,
                       "images": [ph(f"{brand} #{i + 1}", color) for i in range(n_img)]},
        "below_fold": {"aplus_images": [ph(f"{brand} A+ {i + 1}", color) for i in range(n_aplus)], "aplus_text": desc, "description": desc,
                       "spec_table": spec, "customers_say": "Customers like the texture and fragrance.", "rating_histogram": {"5": 60, "4": 20, "3": 10, "2": 5, "1": 5},
                       "reviews": [], "review_images": [ph(f"{brand} review", color)], "brand_story_images": [], "comparison_table": []},
    }


def build():
    g = product("DEMO0001", "Garnier", "DEMO Garnier Bright Complete Vitamin C Moisturizer 50 ml, SPF 30", 300, 50, "ml", 4.2, 3200, "#2e7d32", 5, 3,
                ["With Vitamin C", "SPF 30 protection"], {"Item Form": "Cream", "Skin Type": "All"}, "Garnier DEMO description.")
    comps = [
        product("DEMO0002", "BrandA", "DEMO BrandA Niacinamide Hyaluronic Moisturizer 50 ml, Dermatologist tested, Paraben free", 330, 50, "ml", 4.3, 21000, "#1565c0", 8, 6,
                ["10% Niacinamide", "Hyaluronic acid", "Paraben free", "Clinically tested"], {"Item Form": "Gel", "Skin Type": "Oily", "Net Quantity": "50 ml"}, "BrandA " * 60, 1),
        product("DEMO0003", "BrandB", "DEMO BrandB Ceramide Moisturizer 100 ml", 590, 100, "ml", 4.4, 9800, "#6a1b9a", 6, 4,
                ["Ceramide barrier repair", "Fragrance free"], {"Item Form": "Cream", "Skin Type": "Dry"}, "BrandB " * 40),
        product("DEMO0004", "BrandC", "DEMO BrandC Aloe Vera Gel Moisturizer 150 ml", 900, 150, "ml", 4.0, 12000, "#ef6c00", 4, 0,
                ["Aloe vera", "24 hr hydration"], {"Item Form": "Gel"}, "BrandC short copy."),
    ]
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "marketplace": "amazon.in (DEMO — synthetic data)", "scrape_tolerance_pct": 40, "demo": True,
            "groups": [{"category": "moisturizer", "garnier": g, "competitors": comps}]}
