"""Amazon competitor scraper for Garnier (Playwright).

  python scraper.py --domain amazon.in --tolerance 40 --pages 3 --headful

Writes data.json (resumable: detail pages are cached in .cache/).
Only use on pages/volumes you are permitted to access; Amazon's ToS restricts
automated access. For production-scale use prefer a data provider/API.
"""
import argparse, hashlib, json, random, re, sys, time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from playwright.sync_api import sync_playwright

import parsing as P

CACHE = Path(".cache")

SEARCH_JS = r"""
() => [...document.querySelectorAll('div[data-component-type="s-search-result"]')].map(el => {
  const q = s => el.querySelector(s);
  const label = [...el.querySelectorAll('[aria-label]')].map(e => e.getAttribute('aria-label'))
      .find(a => /ratings?\b/i.test(a) && /\d/.test(a) && !/out of/i.test(a));
  const ratingAlt = (q('span.a-icon-alt') || {}).textContent || '';
  const cnt = label || (q('span.s-underline-text') || {}).textContent || '';
  const img = q('img.s-image');
  return {
    asin: el.getAttribute('data-asin'),
    title: ((q('h2') || {}).innerText || '').trim(),
    price_text: (q('.a-price .a-offscreen') || {}).textContent || '',
    rating_text: ratingAlt, count_text: cnt,
    image: img ? img.src : '', sponsored: !!q('.puis-sponsored-label-text, [aria-label*="Sponsored"]'),
  };
}).filter(r => r.asin && r.title)
"""

DETAIL_JS = r"""
() => {
  const t = s => ((document.querySelector(s) || {}).innerText || '').trim();
  const big = u => u ? u.replace(/\._[A-Za-z0-9,_\-]+_\./, '.') : '';
  const imgs = root => [...document.querySelectorAll(root + ' img')].map(i => {
      const u = i.getAttribute('data-src') || i.getAttribute('data-a-hires') || i.src || '';
      return big(u);
    }).filter(u => u.startsWith('http') && !/pixel|sprite|transparent|grey-pixel|\.gif/i.test(u));
  const uniq = a => [...new Set(a)];
  const kv = sel => { const o = {}; document.querySelectorAll(sel).forEach(r => {
      const k = (r.querySelector('th, td.label, .a-text-bold') || {}).innerText, v = (r.querySelector('td:last-child, td.value, span:last-child') || {}).innerText;
      if (k && v && k !== v) o[k.replace(/[\s:\u200e\u200f]+$/g, '').trim()] = v.trim(); }); return o; };

  // gallery (above the fold) — prefer embedded JSON with hi-res urls
  let gallery = [];
  const html = document.documentElement.innerHTML;
  const m = html.match(/["']colorImages["']\s*:\s*\{\s*["']initial["']\s*:\s*(\[.*?\])\s*\}\s*,/s);
  if (m) { try { gallery = JSON.parse(m[1].replace(/'/g, '"')).map(x => x.hiRes || x.large || '').filter(Boolean); } catch (e) {} }
  if (!gallery.length) gallery = imgs('#altImages');
  const lines = a => a.map(s => s.innerText.trim()).filter(Boolean);

  const reviews = [...document.querySelectorAll('[data-hook="review"]')].slice(0, 10).map(r => ({
      title: ((r.querySelector('[data-hook="review-title"]') || {}).innerText || '').trim(),
      rating: ((r.querySelector('[data-hook$="review-star-rating"]') || {}).textContent || '').trim(),
      body: ((r.querySelector('[data-hook="review-body"]') || {}).innerText || '').trim(),
      images: [...r.querySelectorAll('img[data-hook="review-image-tile"]')].map(i => big(i.src)) }));
  const hist = {}; document.querySelectorAll('#histogramTable tr').forEach(r => {
      const s = r.innerText.replace(/\s+/g, ' ').trim(); const mm = s.match(/(\d) star.*?(\d+)%/i); if (mm) hist[mm[1]] = +mm[2]; });
  const cmp = [...document.querySelectorAll('#HLCXComparisonTable tr')].map(r => [...r.children].map(c => c.innerText.trim()));

  return {
    above_fold: {
      title: t('#productTitle'), brand: t('#bylineInfo'),
      price_text: t('.a-price .a-offscreen') || t('#corePrice_feature_div .a-offscreen'),
      mrp_text: t('.basisPrice .a-offscreen'), discount: t('.savingsPercentage'),
      rating_text: t('#acrPopover'), ratings_text: t('#acrCustomerReviewText'),
      bought_past_month: t('#social-proofing-faceout-title-tk_bought'),
      badges: uniq([t('#acBadge_feature_div'), t('#zeitgeistBadge_feature_div'), t('#dealBadge_feature_div'), t('[data-csa-c-content-id*="coupon"]')].filter(Boolean)),
      bullets: lines([...document.querySelectorAll('#feature-bullets li span.a-list-item')]),
      overview: kv('#productOverview_feature_div tr'),
      images: uniq(gallery), video_count: document.querySelectorAll('#altImages .videoThumbnail').length,
      variants: lines([...document.querySelectorAll('#variation_size_name li, #variation_color_name li')]).slice(0, 20),
    },
    below_fold: {
      aplus_images: uniq(imgs('#aplus')), aplus_text: t('#aplus'),
      brand_story_images: uniq(imgs('#aplusBrandStory_feature_div')), brand_story_text: t('#aplusBrandStory_feature_div'),
      description: t('#productDescription'),
      spec_table: Object.assign({}, kv('#productDetails_techSpec_section_1 tr'), kv('#productDetails_detailBullets_sections1 tr'), kv('#prodDetails table tr')),
      detail_bullets: lines([...document.querySelectorAll('#detailBullets_feature_div li')]),
      important_info: t('#important-information'), comparison_table: cmp,
      customers_say: t('#product-summary'), rating_histogram: hist, reviews: reviews,
      review_images: uniq(reviews.flatMap(r => r.images).concat(imgs('#cr-media-carousel-container, #cm_cr_carousel_images_section'))),
      qa_present: !!document.querySelector('#ask-btf_feature_div'),
    }
  };
}
"""


def sleep(a=1.5, b=3.5):
    time.sleep(random.uniform(a, b))


def guard_captcha(page, headful):
    if page.query_selector("#captchacharacters") or "Robot Check" in page.title():
        if not headful:
            sys.exit("Amazon served a CAPTCHA. Re-run with --headful and solve it once (cookies persist).")
        print("  CAPTCHA — solve it in the browser window…")
        page.wait_for_selector("#captchacharacters", state="detached", timeout=300_000)


def goto(page, url, headful):
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    guard_captcha(page, headful)


def parse_card(r):
    price = P.parse_price(r["price_text"])
    qty, unit = P.parse_size(r["title"])
    return {
        "asin": r["asin"], "title": r["title"], "image": r["image"], "sponsored": r["sponsored"],
        "price": price, "size_qty": qty, "unit": unit, "unit_price": P.unit_price(price, qty),
        "rating": P.parse_rating(r["rating_text"]), "ratings_count": P.parse_count(r["count_text"]) or 0,
    }


def search(page, domain, query, pages, headful):
    out, seen = [], set()
    for p in range(1, pages + 1):
        goto(page, f"https://www.{domain}/s?k={quote_plus(query)}&page={p}", headful)
        try:
            page.wait_for_selector('div[data-component-type="s-search-result"]', timeout=15_000)
        except Exception:
            break
        for r in page.evaluate(SEARCH_JS):
            if r["asin"] not in seen:
                seen.add(r["asin"]); out.append(parse_card(r))
        sleep()
    return out


def scroll_all(page):
    for _ in range(14):
        page.mouse.wheel(0, 1400); page.wait_for_timeout(450)
    page.evaluate("window.scrollTo(0,0)")


def detail(page, domain, card, headful):
    f = CACHE / f"{card['asin']}.json"
    if f.exists():
        return json.loads(f.read_text())
    goto(page, f"https://www.{domain}/dp/{card['asin']}", headful)
    page.wait_for_selector("#productTitle", timeout=20_000)
    scroll_all(page)
    d = page.evaluate(DETAIL_JS)
    d.update(card, url=f"https://www.{domain}/dp/{card['asin']}")
    CACHE.mkdir(exist_ok=True); f.write_text(json.dumps(d))
    sleep()
    return d


def run_scrape(o, log=print, on_data=lambda d: None, stop=lambda: False):
    """o: dict(domain, pages, tolerance, max_competitors, categories, headful). Calls on_data(data) after each group."""
    out = {"generated_at": None, "marketplace": o["domain"], "scrape_tolerance_pct": o["tolerance"], "demo": False, "groups": []}
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            ".browser-profile", headless=not o["headful"], locale="en-IN", viewport={"width": 1366, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        garnier = {}
        queries = ["garnier"] + [f"garnier {P.category_query(c[0])}" for c in P.CATEGORIES
                                 if not o["categories"] or c[0] in o["categories"]]
        for n, q in enumerate(queries, 1):
            if stop(): break
            log(f"Discovering Garnier products ({n}/{len(queries)}): {q}")
            for c in search(page, o["domain"], q, o["pages"] if q == "garnier" else 1, o["headful"]):
                if P.is_garnier(c["title"]) and c["unit_price"]:
                    c["category"] = P.infer_category(c["title"])
                    if c["category"] and (not o["categories"] or c["category"] in o["categories"]):
                        garnier[c["asin"]] = c
        log(f"{len(garnier)} Garnier products with a parseable size")
        pools = {}
        for k, g in enumerate(sorted(garnier.values(), key=lambda x: (x["category"], x["unit_price"])), 1):
            if stop(): break
            cat = g["category"]
            if cat not in pools:
                log(f"Searching category: {cat}")
                pools[cat] = search(page, o["domain"], P.category_query(cat), o["pages"], o["headful"])
            comps = P.select_competitors(g, pools[cat], o["tolerance"])[: o["max_competitors"]]
            log(f"[{k}/{len(garnier)}] {g['title'][:55]} ₹{g['unit_price']}/{g['unit']} → {len(comps)} competitors; fetching pages")
            try:
                gd = detail(page, o["domain"], g, o["headful"])
                cd = []
                for c in comps:
                    d = detail(page, o["domain"], c, o["headful"])
                    d["unit_price"], d["unit"] = c["unit_price"], c["unit"]
                    cd.append(d)
            except Exception as e:  # one bad page shouldn't kill the run
                log(f"  skipped: {str(e)[:120]}"); continue
            gd["category"] = cat
            out["groups"].append({"category": cat, "garnier": gd, "competitors": cd})
            out["generated_at"] = datetime.now().isoformat(timespec="seconds")
            on_data(out)
        ctx.close()
    out["generated_at"] = datetime.now().isoformat(timespec="seconds")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="amazon.in")
    ap.add_argument("--pages", type=int, default=3)
    ap.add_argument("--tolerance", type=float, default=40)
    ap.add_argument("--max-competitors", type=int, default=8)
    ap.add_argument("--categories", nargs="*")
    ap.add_argument("--headful", action="store_true")
    ap.add_argument("--out", default="data.json")
    a = ap.parse_args()
    data = run_scrape(dict(domain=a.domain, pages=a.pages, tolerance=a.tolerance, max_competitors=a.max_competitors,
                           categories=a.categories, headful=a.headful))
    Path(a.out).write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
