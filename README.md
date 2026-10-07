# Garnier competitor dashboard (Amazon)

```bash
pip install -r requirements.txt && playwright install chromium
python scraper.py --domain amazon.in --headful      # -> data.json (solve a CAPTCHA once if shown)
python build_dashboard.py                           # -> dashboard.html (open in a browser)
python build_dashboard.py --demo                    # layout preview with synthetic data
python -c "import test_parsing as t; [getattr(t,n)() for n in dir(t) if n.startswith('test_')]"
```

Logic: every Garnier listing → category → price per ml/g → competitors in the same category within ±tolerance
of that price/unit **and** with more ratings than the Garnier product → above-the-fold (gallery, title, bullets,
badges, overview) and below-the-fold (A+ images/text, description, specs, reviews) are scraped and compared.
Tolerance can be narrowed live in the dashboard.

## Web app (no manual steps after launch)
```bash
pip install -r requirements.txt && playwright install chromium
python app.py        # opens http://localhost:8000 — set options, click "Run analysis", results stream into the dashboard
```

## Which Garnier products are analysed
The five products in `garnier_products.py`, named from the pack shots in `garnier_images/`. Each is looked up on
Amazon by name; its competitors come from its category (3 creams → moisturizer, serum cleanser → face wash,
Super UV → sunscreen). 1 g is treated as 1 ml when comparing price per unit. The dashboard shows no scraped
images: every image slot is an emoji tile that opens the product page, and Garnier shows the supplied pack shot.
To add a product, add a row to `PRODUCTS` and drop its image into `garnier_images/`.
