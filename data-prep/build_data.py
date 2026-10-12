"""Reformat the raw ALA + ABS extracts into tidy, chart-ready files for the Vega-Lite page.

No values are invented: every number below comes from raw/ (ALA biocache facet counts or the
ABS Data API) or is a direct arithmetic derivation of them (shares, ranks, density = ERP / area).
"""
import csv, json, os
from shapely.geometry import shape, mapping, box
from shapely.ops import transform  # noqa
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))          # data-prep/
ROOT = os.path.dirname(HERE)                               # repository root
RAW, GEO, OUT = os.path.join(HERE, "raw"), os.path.join(HERE, "geo"), os.path.join(ROOT, "data")
os.makedirs(OUT, exist_ok=True)

GROUP = {"Aves": "Birds", "Mammalia": "Mammals", "Reptilia": "Reptiles", "Insecta": "Insects"}
SHORT = {"Greater Sydney": "Sydney", "Greater Melbourne": "Melbourne", "Greater Brisbane": "Brisbane",
         "Greater Perth": "Perth", "Greater Adelaide": "Adelaide", "Greater Hobart": "Hobart",
         "Greater Darwin": "Darwin", "Australian Capital Territory": "Canberra"}
# CBD coordinates, used only to place each city's symbol on the national map
CBD = {"Sydney": (-33.87, 151.21), "Melbourne": (-37.81, 144.96), "Brisbane": (-27.47, 153.03),
       "Perth": (-31.95, 115.86), "Adelaide": (-34.93, 138.60), "Hobart": (-42.88, 147.33),
       "Darwin": (-12.46, 130.84), "Canberra": (-35.28, 149.13)}
REMOTE = ["Major Cities of Australia", "Inner Regional Australia", "Outer Regional Australia",
          "Remote Australia", "Very Remote Australia"]
REMOTE_SHORT = {"Major Cities of Australia": "Major cities", "Inner Regional Australia": "Inner regional",
                "Outer Regional Australia": "Outer regional", "Remote Australia": "Remote",
                "Very Remote Australia": "Very remote"}


def write_csv(name, rows, fields):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


# ---------- ABS population ----------
abs_lines = open(os.path.join(RAW, "abs_erp_2025.txt")).read().strip().split("\n")
pop_city, pop_lga = {}, {}
for line in abs_lines:
    if line.startswith("GCCSA|"):
        for x in line[6:].split(";"):
            code, name, v = x.split("~"); pop_city[SHORT[name]] = int(v)
    elif line.startswith("LGA|"):
        for x in line[4:].split(";"):
            code, name, v = x.split("~"); pop_lga[name] = (code, int(v))

# ---------- 1. city x group summary ----------
summary = json.load(open(os.path.join(RAW, "ala_summary_2020_2024.json")))
city_rows, remote_rows = [], []
for lvl, area, cls, rec, sp, intro_rec, intro_sp, thr in summary:
    if lvl == "city":
        c = SHORT[area]
        city_rows.append({"city": c, "lat": CBD[c][0], "lon": CBD[c][1], "group": GROUP[cls],
                          "records": rec, "species": sp, "threatened_species": thr,
                          "population_2025": pop_city[c]})
    else:
        remote_rows.append({"remoteness": REMOTE_SHORT[area], "order": REMOTE.index(area) + 1,
                            "group": GROUP[cls], "records": rec, "species": sp,
                            "threatened_species": thr})
# index richness to Major cities = 100 for the slope chart
base = {r["group"]: r["species"] for r in remote_rows if r["order"] == 1}
for r in remote_rows:
    r["species_index"] = round(100 * r["species"] / base[r["group"]], 1)
    r["records_per_species"] = round(r["records"] / r["species"], 1)
write_csv("city_group_summary.csv", city_rows, list(city_rows[0]))
write_csv("remoteness_group_summary.csv", remote_rows, list(remote_rows[0]))

# ---------- 2. waffle: share of records vs share of species, Major Cities ----------
mc = [r for r in remote_rows if r["order"] == 1]
order = ["Birds", "Mammals", "Reptiles", "Insects"]
waffle = []
for metric in ("records", "species"):
    tot = sum(r[metric] for r in mc)
    vals = {r["group"]: r[metric] for r in mc}
    # largest-remainder rounding so each waffle has exactly 100 squares
    raw = {g: 100 * vals[g] / tot for g in order}
    alloc = {g: int(raw[g]) for g in order}
    for g in sorted(order, key=lambda g: raw[g] - alloc[g], reverse=True)[: 100 - sum(alloc.values())]:
        alloc[g] += 1
    i = 0
    for g in order:
        for _ in range(alloc[g]):
            waffle.append({"metric": "Share of sightings" if metric == "records" else "Share of species",
                           "cell": i, "col": i % 10, "row": i // 10, "group": g,
                           "group_value": vals[g], "group_pct": round(raw[g], 1)})
            i += 1
write_csv("waffle_records_vs_species.csv", waffle, list(waffle[0]))

# ---------- 3. months ----------
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
mrows = []
for line in open(os.path.join(RAW, "ala_month_city_group_2020_2024.txt")).read().strip().split("\n")[1:]:
    city, cls, vals, _ns = line.split("|")
    v = [int(x) for x in vals.split(",")]
    tot = sum(v)
    for i, n in enumerate(v):
        mrows.append({"city": SHORT[city], "group": GROUP[cls], "month": i + 1, "month_name": MONTHS[i],
                      "records": n, "share_of_year": round(100 * n / tot, 2),
                      "index_vs_avg": round(n / (tot / 12), 3)})
write_csv("monthly_records_city_group.csv", mrows, list(mrows[0]))

# ---------- 4. top species ----------
# Author's classification of well-known introduced (non-native) vertebrates appearing in the top-10 lists.
INTRODUCED = {"Vulpes vulpes", "Oryctolagus cuniculus", "Cervus unicolor", "Rattus rattus", "Mus musculus",
              "Felis catus", "Sus scrofa", "Bubalus bubalis", "Acridotheres tristis", "Spilopelia chinensis",
              "Turdus merula", "Sturnus vulgaris", "Passer domesticus", "Hemidactylus frenatus",
              "Apis mellifera", "Pieris rapae", "Bombus terrestris",
              "Cyclocephala signaticollis"}
trows = []
for line in open(os.path.join(RAW, "ala_top10_species_city_group_2020_2024.txt")).read().strip().split("\n"):
    city, cls, items = line.split("|")
    c = SHORT[city]
    grp_total = next(r["records"] for r in city_rows if r["city"] == c and r["group"] == GROUP[cls])
    for rank, it in enumerate(items.split(";"), 1):
        sci, common, n = it.split("~")
        trows.append({"city": c, "group": GROUP[cls], "rank": rank, "scientific_name": sci,
                      "common_name": common or sci, "records": int(n),
                      "share_of_group_records": round(100 * int(n) / grp_total, 2),
                      "origin": "Introduced" if sci in INTRODUCED else "Native"})
write_csv("top10_species_city_group.csv", trows, list(trows[0]))

# ---------- 5. years + providers ----------
yrows, prow = [], []
for line in open(os.path.join(RAW, "ala_year_and_providers.txt")).read().strip().split("\n"):
    if line.startswith("YEAR|"):
        _, cls, vals = line.split("|")
        v = [int(x) for x in vals.split(",")]
        for i, n in enumerate(v):
            y = 2010 + i
            yrows.append({"year": y, "group": GROUP[cls], "records": n,
                          "index_2015": round(100 * n / v[5], 1),
                          "partial": "yes" if y == 2025 else "no"})
    elif line.startswith("DR|"):
        _, cls, items = line.split("|")
        for it in items.split(";"):
            name, n = it.split("~")
            prow.append({"group": GROUP[cls], "provider": name, "records": int(n)})
write_csv("records_by_year_group.csv", yrows, list(yrows[0]))
write_csv("data_providers_group.csv", prow, list(prow[0]))
# hierarchical form of the same rows for the Vega treemap (root -> group -> dataset)
tree = [{"id": "root", "parent": None, "name": "All records", "group": None, "records": None}]
for g in order:
    tree.append({"id": g, "parent": "root", "name": g, "group": g, "records": None})
for r in prow:
    tree.append({"id": r["group"] + "|" + r["provider"], "parent": r["group"], "name": r["provider"],
                 "group": r["group"], "records": r["records"]})
json.dump(tree, open(os.path.join(OUT, "data_providers_tree.json"), "w"), indent=1)

# ---------- 6. geography ----------
to_albers = Transformer.from_crs("EPSG:4326", "EPSG:3577", always_xy=True).transform  # GDA94 Australian Albers

lga_raw = open(os.path.join(RAW, "ala_lga_capitals_2020_2024.txt")).read().strip().split("\n")
hdr = lga_raw[0].split("|")
lga_ala = {}
for line in lga_raw[1:]:
    d = dict(zip(hdr, line.split("|")))
    lga_ala[d["lga"]] = d

adm2 = json.load(open(os.path.join(GEO, "geoBoundaries-AUS-ADM2_simplified.geojson")))
RENAME = {"Moreland": "Merri-bek"}  # renamed in 2022; same boundary
feats, lrows = [], []
for f in adm2["features"]:
    nm = RENAME.get(f["properties"]["shapeName"], f["properties"]["shapeName"])
    if nm not in lga_ala:
        continue
    d = lga_ala[nm]
    geom = shape(f["geometry"])
    area = transform(to_albers, geom).area / 1e6
    code, pop = pop_lga[nm]
    city = SHORT[d["city"]]
    label = "ACT (whole territory)" if nm == "Unincorporated ACT" else nm
    row = {"city": city, "lga": label, "lga_code_2025": code, "population_2025": pop,
           "area_km2": round(area, 1), "density_per_km2": round(pop / area, 1)}
    for k, g in (("Aves", "birds"), ("Mam", "mammals"), ("Rep", "reptiles"), ("Ins", "insects")):
        row[f"records_{g}"] = int(d["rec" + k])
        row[f"species_{g}"] = int(d["sp" + k])
    row["threatened_species"] = int(d["thrSp"])
    lrows.append(row)
    feats.append({"type": "Feature", "properties": {"lga": label, "city": city},
                  "geometry": mapping(geom)})
lrows.sort(key=lambda r: (r["city"], r["lga"]))
write_csv("lga_population_and_wildlife.csv", lrows, list(lrows[0]))
json.dump({"type": "FeatureCollection", "features": feats},
          open(os.path.join(GEO, "capital_lgas_full.geojson"), "w"))

adm1 = json.load(open(os.path.join(GEO, "geoBoundaries-AUS-ADM1_simplified.geojson")))
adm1["features"] = [f for f in adm1["features"] if f["properties"]["shapeName"] != "Other Territories"]
for f in adm1["features"]:
    f["properties"] = {"state": f["properties"]["shapeName"]}
json.dump(adm1, open(os.path.join(GEO, "states_full.geojson"), "w"))

# ---------- 7. Melbourne 0.02-degree grid -> polygons (one 2 km square per ALA facet cell) ----------
cells = []
for x in open(os.path.join(RAW, "ala_melbourne_grid_0.02deg_2020_2024.txt")).read().strip().split(";"):
    a, b, n = map(int, x.split())
    lat, lon = -a / 50, b / 50  # ALA point-0.02 facet = coordinate rounded to 0.02 deg (cell centre)
    r = lambda v: round(v, 2)
    ring = [[r(lon - .01), r(lat - .01)], [r(lon - .01), r(lat + .01)], [r(lon + .01), r(lat + .01)],
            [r(lon + .01), r(lat - .01)], [r(lon - .01), r(lat - .01)]]  # clockwise, as d3-geo expects
    cells.append({"type": "Feature", "properties": {"records": n, "lat": r(lat), "lon": r(lon)},
                  "geometry": {"type": "Polygon", "coordinates": [ring]}})
json.dump({"type": "FeatureCollection", "features": cells},
          open(os.path.join(OUT, "melbourne_grid.geojson"), "w"), separators=(",", ":"))
print("grid cells:", len(cells), "records:", sum(c["properties"]["records"] for c in cells))
