import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# =========================
# CONFIG
# =========================

HTML_FILE = "ttw2026.html"
OUT_DIR = "luma2026"

os.makedirs(OUT_DIR, exist_ok=True)

# =========================
# LOAD HTML
# =========================

with open(HTML_FILE, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# =========================
# HELPERS
# =========================

def is_luma(url):
    return bool(re.search(r"https?://(www\.)?(lu\.ma|luma\.com)/", url or "", re.I))

def extract_slug(url):
    if not url:
        return None

    path = urlparse(url).path.strip("/")
    return path.split("/")[-1].strip() if path else None

# =========================
# COLLECT UNIQUE SLUGS
# =========================

slugs = sorted({
    extract_slug(a.get("href"))
    for a in soup.select("a[href]")
    if is_luma(a.get("href")) and extract_slug(a.get("href"))
})

print(f"Found {len(slugs)} unique slugs")

# =========================
# ONLY DOWNLOAD MISSING FILES
# =========================

to_download = []

for slug in slugs:
    file_path = os.path.join(OUT_DIR, f"{slug}.html")

    if not os.path.exists(file_path):
        to_download.append(slug)

print(f"Need to download {len(to_download)} pages")

# =========================
# HTTP
# =========================

headers = {
    "User-Agent": "Mozilla/5.0"
}

def fetch(url):
    try:
        r = requests.get(url, headers=headers, timeout=25)

        # skip missing pages
        if r.status_code == 404:
            print(f"404 skipped → {url}")
            return None

        r.raise_for_status()

        return r.text

    except Exception as e:
        print(f"Request failed → {url}")
        print(e)
        return None

# =========================
# RANDOM DELAY
# =========================

def human_sleep():
    return random.uniform(10, 20)

# =========================
# DOWNLOAD LOOP
# =========================

for i, slug in enumerate(to_download):
    url = f"https://lu.ma/{slug}"
    file_path = os.path.join(OUT_DIR, f"{slug}.html")

    print(f"[{i+1}/{len(to_download)}] Downloading {slug}")

    html = fetch(url)

    # skip failed pages and continue
    if not html:
        continue

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html)

    sleep_time = human_sleep()

    print(f"Sleeping {sleep_time:.1f}s\n")

    time.sleep(sleep_time)

print("Done.")