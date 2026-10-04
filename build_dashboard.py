"""Embed data.json into dashboard_template.html -> dashboard.html (single self-contained file)."""
import argparse, json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data.json")
ap.add_argument("--out", default="dashboard.html")
ap.add_argument("--demo", action="store_true", help="use synthetic demo data")
a = ap.parse_args()

if a.demo:
    import demo_data
    data = demo_data.build()
else:
    data = json.loads(Path(a.data).read_text())
html = Path("dashboard_template.html").read_text().replace("/*__DATA__*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
Path(a.out).write_text(html)
print("wrote", a.out)
