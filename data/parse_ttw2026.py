import os
import json
import re
from bs4 import BeautifulSoup

INPUT_DIR = "luma2026"
OUTPUT_FILE = "ttw2026.geojson"


# =========================
# FIND JSON-LD EVENT
# =========================
def find_schema_event(obj):
    if isinstance(obj, dict):
        if obj.get("@type") == "Event" and obj.get("@context") == "https://schema.org":
            return obj

        for v in obj.values():
            found = find_schema_event(v)
            if found:
                return found

    elif isinstance(obj, list):
        for i in obj:
            found = find_schema_event(i)
            if found:
                return found

    return None


# =========================
# RAW GEO_ADDRESS_INFO EXTRACT
# =========================
def extract_geo_address_info(html):
    match = re.search(r'"geo_address_info"\s*:\s*(\{.*?\})', html)
    if not match:
        return {}

    try:
        return json.loads(match.group(1))
    except:
        return {}


# =========================
# PARSE SCHEMA EVENT
# =========================
def parse_schema_event(schema):
    if not schema:
        return None

    location = schema.get("location", {})
    if not isinstance(location, dict):
        location = {}

    geo = location.get("geo", {})
    if not isinstance(geo, dict):
        geo = {}

    lat = geo.get("latitude") or geo.get("lat")
    lon = geo.get("longitude") or geo.get("lng")

    if lat is None or lon is None:
        lat = location.get("latitude")
        lon = location.get("longitude")

    coords = [lon, lat] if lat is not None and lon is not None else None

    address = None
    if isinstance(location.get("address"), dict):
        address = location["address"].get("streetAddress")

    if not address:
        address = location.get("name")

    return {
        "url": schema.get("url") or schema.get("@id"),
        "slug": (schema.get("url") or schema.get("@id") or "").split("/")[-1],
        "start": schema.get("startDate"),
        "end": schema.get("endDate"),
        "title": schema.get("name"),
        "description": schema.get("description"),
        "address": address,
        "coords": coords,
        "cover": (
            schema.get("image")[0]
            if isinstance(schema.get("image"), list)
            else schema.get("image")
        ),
        "api_id": schema.get("@id"),
        "type": "event"
    }


# =========================
# EXTRACT FROM FILE
# =========================
def extract_schema_from_file(html):
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script"):
        if not script.string:
            continue

        text = script.string.strip()

        if '"@type"' not in text or "Event" not in text:
            continue

        try:
            data = json.loads(text)
        except:
            continue

        event = find_schema_event(data)
        if event:
            return event

    return None


# =========================
# MAIN LOOP
# =========================
files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".html")]

features = []
missing = []

for file in files:
    path = os.path.join(INPUT_DIR, file)

    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    schema = extract_schema_from_file(html)
    geo_address_info = extract_geo_address_info(html)   # ✅ ADDED HERE

    if not schema:
        missing.append(file)
        continue

    event = parse_schema_event(schema)

    if not event:
        missing.append(file)
        continue

    features.append({
        "type": "Feature",
        "properties": {
            "url": event["url"],
            "slug": event["slug"],
            "start": event["start"],
            "end": event["end"],
            "title": event["title"],
            "description": event["description"],
            "address": event["address"],
            "cover": event["cover"],
            "api_id": event["api_id"],
            "geo_address_info": geo_address_info,  # ✅ ADDED HERE
            "type": "event"
        },
        "geometry": {
            "type": "Point",
            "coordinates": event["coords"]
        }
    })


# =========================
# OUTPUT GEOJSON
# =========================
geojson = {
    "type": "FeatureCollection",
    "features": features
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(geojson, f, indent=4, ensure_ascii=False)


# =========================
# REPORT
# =========================
print("\n====================")
print(f"Files scanned: {len(files)}")
print(f"Events parsed: {len(features)}")
print(f"Missing schema: {len(missing)}")
print("====================")