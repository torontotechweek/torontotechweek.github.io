import json

TTW_PATH = "/home/steve/torontotechweek.github.io/data/ttw2026.geojson"
GEN_PATH = "/home/steve/torontotechweek.github.io/data/ttw2026_gen_coordinates.geojson"
OUTPUT_PATH = "/home/steve/torontotechweek.github.io/data/ttw2026_final.geojson"


with open(TTW_PATH, "r", encoding="utf-8") as f:
    ttw = json.load(f)

with open(GEN_PATH, "r", encoding="utf-8") as f:
    gen = json.load(f)


# map generated features by title
gen_map = {}

for feat in gen["features"]:
    props = feat.get("properties", {})
    title = props.get("title") or props.get("name")

    if title:
        gen_map[title] = feat


merged_count = 0

for feat in ttw["features"]:
    coords = feat.get("geometry", {}).get("coordinates")

    # ONLY MERGE NULL COORDINATES
    if coords is not None:
        continue

    props = feat.get("properties", {})
    title = props.get("title") or props.get("name")

    generated_feat = gen_map.get(title)

    if not generated_feat:
        continue

    generated_coords = (
        generated_feat.get("geometry", {})
        .get("coordinates")
    )

    if generated_coords is not None:
        feat["geometry"]["coordinates"] = generated_coords
        merged_count += 1


with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(ttw, f, indent=4, ensure_ascii=False)


print()
print("====================")
print("Merged coordinates:", merged_count)
print("Output:", OUTPUT_PATH)
print("====================")
print()