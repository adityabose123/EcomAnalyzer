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
