"""Generate the Vega-Lite / Vega specifications for the page as pretty-printed JSON files.

Run:  python3 data-prep/make_specs.py
Each spec is self-contained (own config) so it can be opened on its own in the Vega editor.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root
OUT = os.path.join(ROOT, "specs")
os.makedirs(OUT, exist_ok=True)
VL = "https://vega.github.io/schema/vega-lite/v5.json"

# ---- shared design tokens -------------------------------------------------------------
INK, INK2, MUTED, GRID, SURF = "#22211d", "#55534d", "#8a877e", "#e1e4da", "#f5f6f1"
GROUPS = ["Birds", "Mammals", "Reptiles", "Insects"]
GCOL = ["#2a78d6", "#e34948", "#1baf7a", "#eda100"]  # validated all-pairs (dataviz validator)
CITIES = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Hobart", "Darwin"]
FONT = "Source Sans 3"
ALBERS = {"type": "conicEqualArea", "parallels": [-18, -36], "rotate": [-132, 0]}  # Australian Albers (EPSG:3577)
GROUP_COLOR_EXPR = ("{'Birds':'#2a78d6','Mammals':'#e34948','Reptiles':'#1baf7a',"
                    "'Insects':'#eda100'}[grp] || '#4b4a45'")

CONFIG = {
    "font": FONT,
    "background": None,
    "view": {"stroke": None},
    "axis": {"labelColor": INK2, "titleColor": INK2, "labelFontSize": 12, "titleFontSize": 12,
             "titleFontWeight": 600, "gridColor": GRID, "domainColor": "#c9c5ba", "tickColor": "#c9c5ba",
             "labelFont": FONT, "titleFont": FONT},
    "legend": {"labelColor": INK2, "titleColor": INK2, "labelFontSize": 12, "titleFontSize": 12,
               "titleFontWeight": 600, "labelFont": FONT, "titleFont": FONT},
    "header": {"labelColor": INK, "labelFontSize": 14, "labelFontWeight": 600, "labelFont": FONT,
               "titleFontSize": 0},
    "text": {"font": FONT, "color": INK2},
    "tooltip": {"content": "data"},
}
GROUP_SCALE = {"domain": GROUPS, "range": GCOL}


def save(name, spec, vega=False):
    if not vega:
        spec = {"$schema": VL, **spec}
        spec.setdefault("config", CONFIG)
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    print("wrote", name)


# numeric columns of each CSV, parsed explicitly so the specs never depend on type inference
NUMERIC = {
    "city_group_summary.csv": ["lat", "lon", "records", "species", "threatened_species", "population_2025"],
    "lga_population_and_wildlife.csv": ["population_2025", "area_km2", "density_per_km2", "records_birds",
                                        "species_birds", "records_mammals", "species_mammals", "records_reptiles",
                                        "species_reptiles", "records_insects", "species_insects", "threatened_species"],
    "monthly_records_city_group.csv": ["month", "records", "share_of_year", "index_vs_avg"],
    "records_by_year_group.csv": ["year", "records", "index_2015"],
    "remoteness_group_summary.csv": ["order", "records", "species", "threatened_species", "species_index",
                                     "records_per_species"],
    "top10_species_city_group.csv": ["rank", "records", "share_of_group_records"],
    "waffle_records_vs_species.csv": ["cell", "col", "row", "group_value", "group_pct"],
}


def data(name, **fmt):
    d = {"url": f"data/{name}"}
    if name in NUMERIC:
        fmt = {"type": "csv", "parse": {c: "number" for c in NUMERIC[name]}, **fmt}
    if fmt:
        d["format"] = fmt
    return d


# ======================================================================================
# 01  Proportional symbol map - species recorded in each capital (map idiom 1)
# ======================================================================================
LAB_CITIES = ["Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide", "Canberra", "Hobart", "Darwin"]
LAB_DLON = [3.6, -4.2, 3.8, -3.6, -2.6, 2.4, 3.4, 0.0]
LAB_DLAT = [1.3, -2.6, 0.6, 0.3, 2.6, -3.4, 0.0, 2.7]
save("01_symbol_map.vl.json", {
    "description": "Proportional symbol map: number of species recorded in each capital city, 2020-2024.",
    "width": 560, "height": 470,
    "params": [{"name": "grp", "value": "All four groups",
                "bind": {"input": "select", "name": "Animal group  ",
                         "options": ["All four groups"] + GROUPS}}],
    "projection": ALBERS,
    "layer": [
        {"data": data("aus_states.topo.json", type="topojson", feature="aus_states"),
         "mark": {"type": "geoshape", "fill": "#e4e7dc", "stroke": SURF, "strokeWidth": 1.2},
         "encoding": {"tooltip": {"value": None}}},
        {"data": data("city_group_summary.csv"),
         "transform": [
             {"filter": "grp == 'All four groups' || datum.group == grp"},
             {"aggregate": [{"op": "sum", "field": "species", "as": "species"},
                            {"op": "sum", "field": "records", "as": "records"},
                            {"op": "sum", "field": "threatened_species", "as": "threatened"},
                            {"op": "max", "field": "population_2025", "as": "population"}],
              "groupby": ["city", "lat", "lon"]},
             {"calculate": "datum.lon + " + " ".join(f"(datum.city == '{c}' ? {d} : 0) +" for c, d in zip(LAB_CITIES, LAB_DLON)) + " 0", "as": "llon"},
             {"calculate": "datum.lat + " + " ".join(f"(datum.city == '{c}' ? {d} : 0) +" for c, d in zip(LAB_CITIES, LAB_DLAT)) + " 0", "as": "llat"},
         ],
         "layer": [
             {"mark": {"type": "circle", "opacity": 0.72, "stroke": "#ffffff", "strokeWidth": 2,
                       "color": {"expr": GROUP_COLOR_EXPR}},
              "encoding": {
                  "longitude": {"field": "lon", "type": "quantitative"},
                  "latitude": {"field": "lat", "type": "quantitative"},
                  "size": {"field": "species", "type": "quantitative",
                           "scale": {"type": "linear", "zero": True, "range": [0, 3400]},
                           "legend": {"title": "Species recorded", "orient": "top-left",
                                      "symbolFillColor": "#bdb8ab", "symbolStrokeColor": "#ffffff",
                                      "format": ",.0f", "direction": "vertical", "tickCount": 3}},
                  "tooltip": [
                      {"field": "city", "title": "City"},
                      {"field": "species", "title": "Species recorded", "format": ","},
                      {"field": "records", "title": "Sightings (records)", "format": ","},
                      {"field": "threatened", "title": "Threatened species recorded"},
                      {"field": "population", "title": "Population (June 2025)", "format": ","}]}},
             {"mark": {"type": "text", "fontSize": 13, "fontWeight": 700, "color": INK},
              "encoding": {"longitude": {"field": "llon", "type": "quantitative"},
                           "latitude": {"field": "llat", "type": "quantitative"},
                           "text": {"field": "city"}}},
             {"mark": {"type": "text", "fontSize": 12, "dy": 14, "color": INK2},
              "encoding": {"longitude": {"field": "llon", "type": "quantitative"},
                           "latitude": {"field": "llat", "type": "quantitative"},
                           "text": {"field": "species", "format": ","}}},
         ]},
    ],
})

# ======================================================================================
# 02  Marimekko - what each city's recorded species are made of
# ======================================================================================
save("02_marimekko.vl.json", {
    "description": "Marimekko chart: column width = species recorded in each city; segments = share by animal group.",
    "width": 1000, "height": 300,
    "data": data("city_group_summary.csv"),
    "transform": [
        {"calculate": "indexof(" + json.dumps(GROUPS) + ", datum.group)", "as": "gorder"},
        {"joinaggregate": [{"op": "sum", "field": "species", "as": "city_total"}], "groupby": ["city"]},
        {"window": [{"op": "sum", "field": "species", "as": "run"}],
         "sort": [{"field": "city_total", "order": "descending"}, {"field": "city"}, {"field": "gorder"}],
         "frame": [None, 0]},
        {"joinaggregate": [{"op": "max", "field": "run", "as": "cx2"}], "groupby": ["city"]},
        {"calculate": "datum.cx2 - datum.city_total", "as": "cx"},
        {"window": [{"op": "sum", "field": "species", "as": "yrun"}], "groupby": ["city"],
         "sort": [{"field": "gorder"}], "frame": [None, 0]},
        {"calculate": "datum.yrun / datum.city_total", "as": "y2"},
        {"calculate": "(datum.yrun - datum.species) / datum.city_total", "as": "y1"},
        {"calculate": "datum.species / datum.city_total", "as": "share"},
        {"calculate": "(datum.y1 + datum.y2) / 2", "as": "ymid"},
        {"calculate": "(datum.cx + datum.cx2) / 2", "as": "xmid"},
    ],
    "encoding": {"x": {"field": "cx", "type": "quantitative", "axis": None, "scale": {"zero": True, "nice": False}},
                 "y": {"field": "y1", "type": "quantitative", "scale": {"domain": [0, 1]},
                       "axis": {"format": "%", "title": "Share of the city's recorded species", "tickCount": 5,
                                "grid": False}}},
    "layer": [
        {"mark": {"type": "rect", "stroke": SURF, "strokeWidth": 2},
         "encoding": {"x2": {"field": "cx2"}, "y2": {"field": "y2"},
                      "color": {"field": "group", "type": "nominal", "scale": GROUP_SCALE,
                                "legend": {"title": None, "orient": "bottom", "direction": "horizontal", "offset": 28}},
                      "tooltip": [{"field": "city", "title": "City"}, {"field": "group", "title": "Group"},
                                  {"field": "species", "title": "Species recorded", "format": ","},
                                  {"field": "share", "title": "Share of city's species", "format": ".1%"},
                                  {"field": "city_total", "title": "All species in the city", "format": ","}]}},
        {"transform": [{"filter": "datum.share >= 0.05"}],
         "mark": {"type": "text", "fontSize": 12, "fontWeight": 600, "color": "#ffffff"},
         "encoding": {"x": {"field": "xmid", "type": "quantitative"},
                      "y": {"field": "ymid", "type": "quantitative"},
                      "text": {"field": "share", "format": ".0%"}}},
        {"transform": [{"filter": "datum.gorder == 0"}],
         "mark": {"type": "text", "fontSize": 13, "fontWeight": 700, "color": INK, "baseline": "bottom", "dy": -6},
         "encoding": {"x": {"field": "xmid", "type": "quantitative"}, "y": {"datum": 1},
                      "text": {"field": "city"}}},
        {"transform": [{"filter": "datum.gorder == 0"}],
         "mark": {"type": "text", "fontSize": 11, "color": MUTED, "baseline": "top", "dy": 6},
         "encoding": {"x": {"field": "xmid", "type": "quantitative"}, "y": {"datum": 0},
                      "text": {"field": "city_total", "format": ","}}},
    ],
})

# ======================================================================================
# 03  Waffle pair - share of sightings vs share of species (Major Cities, 2020-24)
# ======================================================================================
save("03_waffle.vl.json", {
    "description": "Two waffle charts (100 squares each): share of sightings and share of species by animal group, Australia's major cities, 2020-2024.",
    "data": data("waffle_records_vs_species.csv"),
    "facet": {"column": {"field": "metric", "type": "nominal", "sort": ["Share of sightings", "Share of species"],
                         "header": {"labelFontSize": 15, "labelPadding": 10}}},
    "spacing": 56,
    "spec": {
        "width": {"step": 23}, "height": {"step": 23},
        "mark": {"type": "rect", "cornerRadius": 3, "stroke": SURF, "strokeWidth": 2.5},
        "encoding": {
            "x": {"field": "col", "type": "ordinal", "axis": None},
            "y": {"field": "row", "type": "ordinal", "axis": None},
            "color": {"field": "group", "type": "nominal", "scale": GROUP_SCALE,
                      "legend": {"title": None, "orient": "bottom", "direction": "horizontal"}},
            "tooltip": [{"field": "group", "title": "Group"},
                        {"field": "group_pct", "title": "Percent", "format": ".1f"},
                        {"field": "group_value", "title": "Count", "format": ","}],
        },
    },
    "resolve": {"scale": {"color": "shared"}},
})

# ======================================================================================
# 04  Line chart (log) - records per year, capital cities
# ======================================================================================
save("04_records_by_year.vl.json", {
    "description": "Wildlife records per year in the eight capital cities, by animal group (log scale).",
    "width": 440, "height": 330,
    "data": data("records_by_year_group.csv"),
    "encoding": {
        "x": {"field": "year", "type": "quantitative", "scale": {"domain": [2010, 2025], "nice": False},
              "axis": {"format": "d", "title": None, "values": [2010, 2013, 2016, 2019, 2022, 2025], "grid": False}},
        "y": {"field": "records", "type": "quantitative",
              "scale": {"type": "log", "domain": [2000, 6000000]},
              "axis": {"title": "Records per year (log scale)", "format": "~s", "values": [3000, 10000, 30000, 100000, 300000, 1000000, 3000000]}},
        "color": {"field": "group", "type": "nominal", "scale": GROUP_SCALE,
                  "legend": {"title": "Click to highlight", "orient": "top", "direction": "horizontal"}},
        "opacity": {"condition": {"param": "hl", "value": 1}, "value": 0.15},
    },
    "layer": [
        {"transform": [{"filter": "datum.year <= 2024"}], "mark": {"type": "line", "strokeWidth": 2.5},
         "params": [{"name": "hl", "select": {"type": "point", "fields": ["group"]}, "bind": "legend"}]},
        {"transform": [{"filter": "datum.year >= 2024"}],
         "mark": {"type": "line", "strokeWidth": 2.5, "strokeDash": [4, 4]}},
        {"mark": {"type": "circle", "size": 40, "opacity": 1},
         "encoding": {"tooltip": [{"field": "group", "title": "Group"}, {"field": "year", "title": "Year"},
                                  {"field": "records", "title": "Records", "format": ","},
                                  {"field": "partial", "title": "Year incomplete in ALA?"}]}},
        {"transform": [{"filter": "datum.year == 2025"}],
         "mark": {"type": "text", "align": "left", "dx": 8, "fontSize": 12, "fontWeight": 600},
         "encoding": {"text": {"field": "group"}, "color": {"value": INK2}}},
        {"data": {"values": [{"year": 2025, "records": 4300000, "t": "2025 not yet complete"}]},
         "mark": {"type": "text", "align": "right", "fontSize": 11, "fontStyle": "italic", "color": MUTED, "dx": 4},
         "encoding": {"text": {"field": "t"}, "color": {"value": MUTED}, "opacity": {"value": 1}}},
    ],
})

# ======================================================================================
# 05  Treemap (Vega) - which datasets the urban records come from
# ======================================================================================
save("05_treemap.vg.json", {
    "$schema": "https://vega.github.io/schema/vega/v5.json",
    "description": "Treemap: records from the eight capital cities 2020-2024 by contributing dataset, nested in animal group (top 8 datasets per group).",
    "width": 460, "height": 330, "padding": 2, "autosize": "none",
    "config": {"text": {"font": FONT}, "legend": {"labelFont": FONT}},
    "signals": [{"name": "scale_mode", "value": "sqrt",
                 "bind": {"input": "radio", "options": ["true", "sqrt"],
                          "labels": ["True area", "Square-root (show small datasets)"], "name": "Box size  "}}],
    "data": [
        {"name": "tree", "url": "data/data_providers_tree.json",
         "transform": [
             {"type": "formula", "as": "size", "expr": "datum.records == null ? 0 : (scale_mode == 'sqrt' ? sqrt(datum.records) : datum.records)"},
             {"type": "stratify", "key": "id", "parentKey": "parent"},
             {"type": "treemap", "field": "size", "sort": {"field": "value", "order": "descending"},
              "round": True, "method": "squarify", "ratio": 1.4, "paddingInner": 2, "paddingOuter": 0,
              "paddingTop": {"signal": "18"}, "size": [{"signal": "width"}, {"signal": "height"}]}]},
        {"name": "groups", "source": "tree", "transform": [{"type": "filter", "expr": "datum.depth == 1"}]},
        {"name": "leaves", "source": "tree", "transform": [{"type": "filter", "expr": "datum.depth == 2"}]},
    ],
    "scales": [{"name": "color", "type": "ordinal", "domain": GROUPS, "range": GCOL}],
    "marks": [
        {"type": "rect", "from": {"data": "groups"},
         "encode": {"update": {"x": {"field": "x0"}, "y": {"field": "y0"}, "x2": {"field": "x1"}, "y2": {"field": "y1"},
                               "fill": {"value": "#e8ebe2"}}}},
        {"type": "text", "from": {"data": "groups"},
         "encode": {"update": {"x": {"signal": "datum.x0 + 4"}, "y": {"signal": "datum.y0 + 13"},
                               "text": {"field": "name"}, "fontSize": {"value": 12}, "fontWeight": {"value": 700},
                               "fill": {"value": INK}}}},
        {"type": "rect", "from": {"data": "leaves"},
         "encode": {"update": {"x": {"field": "x0"}, "y": {"field": "y0"}, "x2": {"field": "x1"}, "y2": {"field": "y1"},
                               "fill": {"scale": "color", "field": "group"}, "stroke": {"value": SURF},
                               "strokeWidth": {"value": 1.5}, "cornerRadius": {"value": 3},
                               "fillOpacity": {"value": 0.92},
                               "tooltip": {"signal": "{'Dataset': datum.name, 'Group': datum.group, 'Records': format(datum.records, ',')}"}},
                    "hover": {"fillOpacity": {"value": 0.65}}}},
        {"type": "text", "from": {"data": "leaves"}, "interactive": False,
         "encode": {"update": {"x": {"signal": "datum.x0 + 4"}, "y": {"signal": "datum.y0 + 13"},
                               "text": {"signal": "(datum.x1 - datum.x0) > 70 && (datum.y1 - datum.y0) > 30 ? (length(datum.name) > (datum.x1 - datum.x0) / 6.5 ? slice(datum.name, 0, floor((datum.x1 - datum.x0) / 6.5) - 1) + '…' : datum.name) : ''"},
                               "fontSize": {"value": 11}, "fontWeight": {"value": 600}, "fill": {"value": "#ffffff"}}}},
        {"type": "text", "from": {"data": "leaves"}, "interactive": False,
         "encode": {"update": {"x": {"signal": "datum.x0 + 4"}, "y": {"signal": "datum.y0 + 27"},
                               "text": {"signal": "(datum.x1 - datum.x0) > 70 && (datum.y1 - datum.y0) > 40 ? format(datum.records, '.3s') : ''"},
                               "fontSize": {"value": 11}, "fill": {"value": "#ffffff"}}}},
    ],
}, vega=True)

# ======================================================================================
# 06  Slope graph - species recorded, major cities vs very remote Australia
# ======================================================================================
save("06_slope.vl.json", {
    "description": "Slope graph: species recorded 2020-2024 in Australia's major cities vs very remote areas, by animal group (log scale).",
    "width": 360, "height": 360,
    "data": data("remoteness_group_summary.csv"),
    "transform": [
        {"filter": "datum.order == 1 || datum.order == 5"},
        {"joinaggregate": [{"op": "min", "field": "species", "as": "city_sp"}], "groupby": ["group"]},
        {"calculate": "datum.order == 1 ? 'Major cities' : 'Very remote'", "as": "where"},
    ],
    "encoding": {
        "x": {"field": "where", "type": "ordinal", "sort": ["Major cities", "Very remote"],
              "scale": {"padding": 0.35},
              "axis": {"title": None, "orient": "top", "labelAngle": 0, "labelFontSize": 13, "labelFontWeight": 700,
                       "labelColor": INK, "domain": False, "ticks": False, "labelPadding": 8}},
        "y": {"field": "species", "type": "quantitative", "scale": {"type": "log", "domain": [150, 15000]},
              "axis": None},
        "color": {"field": "group", "type": "nominal", "scale": GROUP_SCALE, "legend": None},
        "opacity": {"condition": [{"param": "hov", "empty": True, "value": 1}], "value": 0.2},
        "tooltip": [{"field": "group", "title": "Group"}, {"field": "where", "title": "Area"},
                    {"field": "species", "title": "Species recorded", "format": ","},
                    {"field": "records", "title": "Records", "format": ","},
                    {"field": "threatened_species", "title": "Threatened species recorded"}],
    },
    "layer": [
        {"mark": {"type": "line", "strokeWidth": 3}, "encoding": {"detail": {"field": "group"}}},
        {"mark": {"type": "circle", "size": 110, "stroke": SURF, "strokeWidth": 2, "opacity": 1},
         "params": [{"name": "hov", "select": {"type": "point", "fields": ["group"], "on": "pointerover", "clear": "pointerout"}}]},
        {"transform": [{"filter": "datum.order == 1"}],
         "mark": {"type": "text", "align": "right", "dx": -12, "fontSize": 12},
         "encoding": {"text": {"field": "species", "format": ","}, "color": {"value": INK2}}},
    ] + [
        {"transform": [{"filter": "datum.order == 5 && " + test},
                       {"calculate": "datum.group + '  ' + format(datum.species, ',') + (datum.group == 'Insects' ? '  (fewer records)' : '  (×' + format(datum.species / datum.city_sp, '.1f') + ')')", "as": "lab"}],
         "mark": {"type": "text", "align": "left", "dx": 12, "dy": dy, "fontSize": 12, "fontWeight": 600},
         "encoding": {"text": {"field": "lab"}, "color": {"value": INK2}}}
        for test, dy in (("datum.group == 'Birds'", 9), ("datum.group == 'Reptiles'", -8),
                         ("(datum.group == 'Mammals' || datum.group == 'Insects')", 0))
    ],
})

# ======================================================================================
# 07  Linked choropleth + scatterplot (map idiom 2) - one spec so the views share selections
# ======================================================================================
VALUE_EXPR = ("grp == 'Birds' ? datum.species_birds : grp == 'Mammals' ? datum.species_mammals : "
              "grp == 'Reptiles' ? datum.species_reptiles : datum.species_insects")
TIP = [{"field": "lga", "title": "Local government area"}, {"field": "city", "title": "City"},
       {"field": "value", "title": "Species recorded (selected group)", "format": ","},
       {"field": "population_2025", "title": "Population (June 2025)", "format": ","},
       {"field": "density_per_km2", "title": "People per km²", "format": ",.0f"},
       {"field": "threatened_species", "title": "Threatened species (all groups)"}]
LGA_FIELDS = ["population_2025", "area_km2", "density_per_km2", "species_birds", "species_mammals",
              "species_reptiles", "species_insects", "threatened_species"]
save("07_choropleth_scatter.vl.json", {
    "description": "Linked views: choropleth of species recorded per local government area for a chosen city, and a scatterplot of every capital-city LGA's population density (ABS) against species recorded (ALA).",
    "params": [
        {"name": "city", "value": "Melbourne",
         "bind": {"input": "select", "options": CITIES[:-3] + ["Hobart", "Darwin"], "name": "City  "}},
        {"name": "grp", "value": "Birds", "bind": {"input": "select", "options": GROUPS, "name": "Animal group  "}},
        {"name": "hov", "select": {"type": "point", "fields": ["lga"], "on": "pointerover", "clear": "pointerout"},
         "views": ["map", "scatterpts"]},
    ],
    "hconcat": [
        {"name": "map", "width": 440, "height": 420,
         "data": data("capital_lgas.topo.json", type="topojson", feature="lgas"),
         "transform": [
             {"calculate": "datum.properties.lga", "as": "lga"},
             {"calculate": "datum.properties.city", "as": "city"},
             {"filter": "datum.city == city"},
             {"lookup": "lga", "from": {"data": data("lga_population_and_wildlife.csv"), "key": "lga",
                                        "fields": LGA_FIELDS}},
             {"calculate": VALUE_EXPR, "as": "value"},
         ],
         "projection": ALBERS,
         "mark": {"type": "geoshape", "stroke": SURF, "strokeWidth": 1},
         "encoding": {
             "color": {"field": "value", "type": "quantitative",
                       "scale": {"scheme": "blues", "zero": False},
                       "legend": {"title": "Species recorded (darker = more)", "orient": "bottom", "direction": "horizontal",
                                  "gradientLength": 220, "format": ",.0f"}},
             "strokeWidth": {"condition": {"param": "hov", "empty": False, "value": 3}, "value": 0.8},
             "stroke": {"condition": {"param": "hov", "empty": False, "value": INK}, "value": SURF},
             "tooltip": TIP}},
        {"name": "scatter", "width": 440, "height": 420,
         "data": data("lga_population_and_wildlife.csv"),
         "transform": [{"calculate": VALUE_EXPR, "as": "value"},
                       {"calculate": "datum.city == city ? 1 : 0", "as": "sel"}],
         "layer": [
             {"mark": {"type": "line", "color": INK2, "strokeDash": [6, 4], "strokeWidth": 1.6},
              "transform": [{"calculate": "log(datum.density_per_km2) / LN10", "as": "logd"},
                            {"regression": "value", "on": "logd", "method": "linear"},
                            {"calculate": "pow(10, datum.logd)", "as": "density_per_km2"}],
              "encoding": {"x": {"field": "density_per_km2", "type": "quantitative"},
                           "y": {"field": "value", "type": "quantitative"}}},
             {"name": "scatterpts", "mark": {"type": "circle", "stroke": "#ffffff", "strokeWidth": 1},
              "encoding": {
                  "x": {"field": "density_per_km2", "type": "quantitative",
                        "scale": {"type": "log", "domain": [10, 10000]},
                        "axis": {"title": "People per km² (log scale) →  more crowded", "format": ",", "values": [10, 30, 100, 300, 1000, 3000, 10000]}},
                  "y": {"field": "value", "type": "quantitative", "scale": {"zero": True},
                        "axis": {"title": "Species recorded (selected group)"}},
                  "color": {"condition": {"test": "datum.city == city", "value": {"expr": GROUP_COLOR_EXPR}},
                            "value": "#d6d1c5"},
                  "size": {"condition": {"param": "hov", "empty": False, "value": 260}, "value": 70},
                  "order": {"field": "sel"},
                  "tooltip": TIP}},
             {"transform": [{"filter": {"param": "hov", "empty": False}}],
              "mark": {"type": "text", "dy": -14, "fontWeight": 700, "fontSize": 12, "color": INK},
              "encoding": {"x": {"field": "density_per_km2", "type": "quantitative"},
                           "y": {"field": "value", "type": "quantitative"}, "text": {"field": "lga"}}},
         ]},
    ],
    "spacing": 40,
})

# ======================================================================================
# 08  Gridded density map - where Melburnians record wildlife (map idiom 3)
# ======================================================================================
save("08_melbourne_grid.vl.json", {
    "description": "Gridded density map: wildlife records 2020-2024 in 2 km x 2 km cells (0.02 degrees) across Greater Melbourne.",
    "width": 540, "height": 440,
    "projection": ALBERS,
    "layer": [
        {"data": data("capital_lgas.topo.json", type="topojson", feature="lgas"),
         "transform": [{"filter": "datum.properties.city == 'Melbourne'"}],
         "mark": {"type": "geoshape", "fill": "#e4e7dc", "stroke": "#ffffff", "strokeWidth": 1},
         "encoding": {"tooltip": {"field": "properties.lga", "title": "Local government area"}}},
        {"data": data("melbourne_grid.geojson", type="json", property="features"),
         "mark": {"type": "geoshape", "stroke": None},
         "encoding": {
             "color": {"field": "properties.records", "type": "quantitative",
                       "scale": {"type": "log", "scheme": "teals", "domain": [1, 100000], "clamp": True},
                       "legend": {"title": "Records per 2 km cell", "format": "~s", "orient": "bottom-right",
                                  "gradientLength": 170, "values": [1, 10, 100, 1000, 10000, 100000]}},
             "tooltip": [{"field": "properties.records", "title": "Records 2020–24", "format": ","},
                         {"field": "properties.lat", "title": "Cell centre latitude"},
                         {"field": "properties.lon", "title": "Cell centre longitude"}]}},
        {"data": {"values": [{"lon": 144.60, "lat": -38.00}, {"lon": 144.98, "lat": -37.82}]},
         "mark": {"type": "circle", "size": 260, "fill": None, "stroke": INK, "strokeWidth": 1.6},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}}},
        {"data": {"values": [{"lon": 144.60, "lat": -38.00, "t": "Western Treatment Plant, Werribee"}]},
         "mark": {"type": "text", "align": "left", "dx": -20, "dy": 26, "fontWeight": 700, "fontSize": 12, "color": "#ffffff", "stroke": "#ffffff", "strokeWidth": 4, "strokeJoin": "round", "opacity": 0.9},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
        {"data": {"values": [{"lon": 144.60, "lat": -38.00, "t": "Western Treatment Plant, Werribee"}]},
         "mark": {"type": "text", "align": "left", "dx": -20, "dy": 26, "fontWeight": 700, "fontSize": 12, "color": INK},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
        {"data": {"values": [{"lon": 144.60, "lat": -38.00, "t": "≈160,000 records — a famous birdwatching wetland"}]},
         "mark": {"type": "text", "align": "left", "dx": -20, "dy": 41, "fontSize": 11.5, "color": "#ffffff", "stroke": "#ffffff", "strokeWidth": 4, "strokeJoin": "round", "opacity": 0.9},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
        {"data": {"values": [{"lon": 144.60, "lat": -38.00, "t": "≈160,000 records — a famous birdwatching wetland"}]},
         "mark": {"type": "text", "align": "left", "dx": -20, "dy": 41, "fontSize": 11.5, "color": INK2},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
        {"data": {"values": [{"lon": 144.98, "lat": -37.82, "t": "Royal Botanic Gardens"}]},
         "mark": {"type": "text", "align": "right", "dx": -10, "dy": 34, "fontWeight": 700, "fontSize": 12, "color": "#ffffff", "stroke": "#ffffff", "strokeWidth": 4, "strokeJoin": "round", "opacity": 0.9},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
        {"data": {"values": [{"lon": 144.98, "lat": -37.82, "t": "Royal Botanic Gardens"}]},
         "mark": {"type": "text", "align": "right", "dx": -10, "dy": 34, "fontWeight": 700, "fontSize": 12, "color": INK},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
        {"data": {"values": [{"lon": 144.98, "lat": -37.82, "t": "≈97,000 records"}]},
         "mark": {"type": "text", "align": "right", "dx": -10, "dy": 49, "fontSize": 11.5, "color": "#ffffff", "stroke": "#ffffff", "strokeWidth": 4, "strokeJoin": "round", "opacity": 0.9},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
        {"data": {"values": [{"lon": 144.98, "lat": -37.82, "t": "≈97,000 records"}]},
         "mark": {"type": "text", "align": "right", "dx": -10, "dy": 49, "fontSize": 11.5, "color": INK2},
         "encoding": {"longitude": {"field": "lon", "type": "quantitative"}, "latitude": {"field": "lat", "type": "quantitative"}, "text": {"field": "t"}}},
    ],
})

# ======================================================================================
# 09  Dot matrix - the birds that top the lists in several cities
# ======================================================================================
save("09_bird_matrix.vl.json", {
    "padding": {"left": 64, "top": 5, "right": 5, "bottom": 5},
    "description": "Dot matrix: birds in the top-10 most-recorded list of at least two capital cities; dot size = share of that city's bird records, number = rank.",
    "width": {"step": 74}, "height": {"step": 30},
    "data": data("top10_species_city_group.csv"),
    "transform": [
        {"filter": "datum.group == 'Birds'"},
        {"joinaggregate": [{"op": "count", "as": "ncities"}, {"op": "sum", "field": "records", "as": "tot"}],
         "groupby": ["common_name"]},
        {"filter": "datum.ncities >= 2"},
        {"calculate": "datum.common_name + ' (' + datum.ncities + ')'", "as": "label"},
        {"calculate": "datum.origin == 'Introduced' ? 'Introduced' : 'Native'", "as": "origin"},
    ],
    "encoding": {
        "x": {"field": "city", "type": "nominal", "sort": CITIES,
              "axis": {"title": None, "orient": "top", "labelAngle": 0, "labelFontSize": 12.5, "labelFontWeight": 700,
                       "labelColor": INK, "domain": False, "ticks": False, "grid": True, "gridColor": "#e8ebe2"}},
        "y": {"field": "label", "type": "nominal",
              "sort": {"field": "tot", "op": "max", "order": "descending"},
              "axis": {"title": None, "labelFontSize": 12.5, "domain": False, "ticks": False, "grid": True,
                       "gridColor": "#e8ebe2", "labelPadding": 8, "labelLimit": 240}},
    },
    "layer": [
        {"mark": {"type": "circle", "stroke": "#ffffff", "strokeWidth": 1},
         "encoding": {"size": {"field": "share_of_group_records", "type": "quantitative",
                               "scale": {"range": [40, 720], "domain": [0, 7]},
                               "legend": {"title": "% of the city's bird records", "orient": "bottom",
                                          "direction": "horizontal", "values": [1, 3, 5],
                                          "symbolFillColor": "#2a78d6"}},
                      "color": {"value": "#2a78d6"},
                      "tooltip": [{"field": "common_name", "title": "Bird"}, {"field": "scientific_name", "title": "Scientific name"},
                                  {"field": "city", "title": "City"}, {"field": "rank", "title": "Rank in city"},
                                  {"field": "records", "title": "Records 2020–24", "format": ","},
                                  {"field": "share_of_group_records", "title": "% of city's bird records", "format": ".1f"}]}},
        {"mark": {"type": "text", "fontSize": 10.5, "fontWeight": 700, "color": "#ffffff"},
         "encoding": {"text": {"field": "rank"}}},
    ],
})

# ======================================================================================
# 10  Small multiples - each city's most-recorded mammals
# ======================================================================================
save("10_mammals_small_multiples.vl.json", {
    "padding": {"left": 36, "top": 5, "right": 5, "bottom": 5},
    "description": "Small multiples: the five most-recorded mammals in each capital, 2020-2024. Grey = introduced species.",
    "data": data("top10_species_city_group.csv"),
    "transform": [{"filter": "datum.group == 'Mammals' && datum.rank <= 5"}],
    "facet": {"field": "city", "type": "nominal", "sort": CITIES, "header": {"labelAlign": "left", "labelAnchor": "start"}},
    "columns": 4, "spacing": {"column": 14, "row": 24},
    "resolve": {"scale": {"y": "independent", "x": "independent"}},
    "spec": {
        "width": 92, "height": 130,
        "encoding": {
            "y": {"field": "common_name", "type": "nominal", "sort": {"field": "records", "order": "descending"},
                  "axis": {"title": None, "domain": False, "ticks": False, "labelLimit": 128, "labelFontSize": 11}},
            "x": {"field": "records", "type": "quantitative", "axis": None},
        },
        "layer": [
            {"mark": {"type": "bar", "cornerRadiusEnd": 4, "height": {"band": 0.72}},
             "encoding": {"color": {"field": "origin", "type": "nominal",
                                    "scale": {"domain": ["Native", "Introduced"], "range": ["#e34948", "#9b978c"]},
                                    "legend": {"title": None, "orient": "top", "direction": "horizontal"}},
                          "tooltip": [{"field": "common_name", "title": "Mammal"},
                                      {"field": "scientific_name", "title": "Scientific name"},
                                      {"field": "records", "title": "Records 2020–24", "format": ","},
                                      {"field": "origin", "title": "Origin"}]}},
            {"mark": {"type": "text", "align": "left", "dx": 4, "fontSize": 11, "color": INK2},
             "encoding": {"text": {"field": "records", "format": ","}}},
        ],
    },
})

# ======================================================================================
# 11  Stacked bar - threatened species recorded per city
# ======================================================================================
save("11_threatened.vl.json", {
    "description": "Stacked horizontal bar: nationally threatened (EPBC-listed) species recorded in each capital, 2020-2024, by group.",
    "width": 460, "height": {"step": 30},
    "data": data("city_group_summary.csv"),
    "transform": [{"calculate": "indexof(" + json.dumps(GROUPS) + ", datum.group)", "as": "gorder"},
                  {"joinaggregate": [{"op": "sum", "field": "threatened_species", "as": "total"}], "groupby": ["city"]}],
    "encoding": {"y": {"field": "city", "type": "nominal", "sort": {"field": "total", "op": "max", "order": "descending"},
                       "axis": {"title": None, "domain": False, "ticks": False, "labelFontSize": 12.5, "labelFontWeight": 600,
                                "labelColor": INK}}},
    "layer": [
        {"mark": {"type": "bar", "stroke": SURF, "strokeWidth": 2, "height": {"band": 0.7}},
         "encoding": {"x": {"field": "threatened_species", "type": "quantitative", "stack": "zero",
                            "axis": {"title": "Threatened species recorded", "grid": True, "tickCount": 5}},
                      "color": {"field": "group", "type": "nominal", "scale": GROUP_SCALE,
                                "legend": {"title": None, "orient": "top", "direction": "horizontal"}},
                      "order": {"field": "gorder"},
                      "tooltip": [{"field": "city"}, {"field": "group"},
                                  {"field": "threatened_species", "title": "Threatened species"},
                                  {"field": "total", "title": "City total (all groups)"}]}},
        {"transform": [{"filter": "datum.gorder == 0"}],
         "mark": {"type": "text", "align": "left", "dx": 6, "fontWeight": 700, "fontSize": 12.5, "color": INK},
         "encoding": {"x": {"field": "total", "type": "quantitative"}, "text": {"field": "total"}}},
    ],
})

# ======================================================================================
# 12  Radial (rose) charts - seasonal rhythm by group for a chosen city
# ======================================================================================
save("12_radial_seasons.vl.json", {
    "description": "Radial (rose) small multiples: records in each month relative to an average month (dashed ring = an average month), for a chosen city. January at 12 o'clock, months run clockwise.",
    "data": data("monthly_records_city_group.csv"),
    "params": [{"name": "city", "value": "Melbourne",
                "bind": {"input": "select", "options": CITIES, "name": "City  "}}],
    "transform": [{"filter": "datum.city == city"},
                  {"calculate": "datum.month - 1", "as": "t0"}, {"calculate": "datum.month", "as": "t1"}],
    "facet": {"column": {"field": "group", "type": "nominal", "sort": GROUPS, "header": {"labelFontSize": 14}}},
    "spacing": 18,
    "spec": {
        "width": 218, "height": 218,
        "encoding": {"theta": {"field": "t0", "type": "quantitative",
                               "scale": {"domain": [0, 12], "range": [0, 6.283185]}},
                     "theta2": {"field": "t1"}},
        "layer": [
            {"mark": {"type": "arc", "stroke": SURF, "strokeWidth": 1.5, "cornerRadius": 2},
             "encoding": {
                 "radius": {"field": "index_vs_avg", "type": "quantitative",
                            "scale": {"type": "sqrt", "zero": True, "range": [4, 96],
                                      "domain": {"expr": "[0, city == 'Darwin' ? 5 : 2.6]"}}},
                 "color": {"field": "group", "type": "nominal", "scale": GROUP_SCALE, "legend": None},
                 "opacity": {"condition": {"test": "datum.index_vs_avg >= 1", "value": 0.95}, "value": 0.4},
                 "tooltip": [{"field": "month_name", "title": "Month"}, {"field": "group", "title": "Group"},
                             {"field": "records", "title": "Records 2020–24", "format": ","},
                             {"field": "index_vs_avg", "title": "× an average month", "format": ".2f"}]}},
            {"transform": [{"filter": "datum.month == 1"}, {"calculate": "0", "as": "t0"}, {"calculate": "12", "as": "t1"}],
             "mark": {"type": "arc", "fill": None, "stroke": INK, "strokeDash": [3, 3], "strokeWidth": 1.2,
                      "tooltip": False},
             "encoding": {"radius": {"datum": 1, "type": "quantitative"}}},
            {"transform": [{"filter": "datum.month == 1 || datum.month == 4 || datum.month == 7 || datum.month == 10"},
                           {"calculate": "datum.month - 0.5", "as": "t0"}],
             "mark": {"type": "text", "fontSize": 11, "fontWeight": 600, "color": MUTED, "radius": 106},
             "encoding": {"theta2": None, "text": {"field": "month_name"}}},
        ],
    },
})

# ======================================================================================
# 13  Heat map - month x city, relative to an average month, chosen group
# ======================================================================================
save("13_season_heatmap.vl.json", {
    "description": "Heat map: records per month relative to that city's average month (1 = average), for a chosen animal group, 2020-2024.",
    "width": {"step": 52}, "height": {"step": 32},
    "data": data("monthly_records_city_group.csv"),
    "params": [{"name": "grp", "value": "Reptiles", "bind": {"input": "select", "options": GROUPS, "name": "Animal group  "}}],
    "transform": [{"filter": "datum.group == grp"}],
    "encoding": {
        "x": {"field": "month_name", "type": "ordinal",
              "sort": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
              "axis": {"title": None, "orient": "top", "labelAngle": 0, "domain": False, "ticks": False, "labelFontSize": 12}},
        "y": {"field": "city", "type": "nominal", "sort": ["Darwin", "Brisbane", "Perth", "Sydney", "Canberra", "Adelaide", "Melbourne", "Hobart"],
              "axis": {"title": None, "domain": False, "ticks": False, "labelFontSize": 12.5, "labelFontWeight": 600,
                       "labelColor": INK, "labelPadding": 6}},
    },
    "layer": [
        {"mark": {"type": "rect", "stroke": SURF, "strokeWidth": 2, "cornerRadius": 3},
         "encoding": {"color": {"field": "index_vs_avg", "type": "quantitative",
                                "scale": {"type": "log", "scheme": "blueorange", "domain": [0.25, 4], "domainMid": 1, "clamp": True},
                                "legend": {"title": "× average month", "titleLimit": 220, "orient": "right", "gradientLength": 200,
                                           "values": [0.25, 0.5, 1, 2, 4], "format": ".2~f"}},
                      "tooltip": [{"field": "city", "title": "City"}, {"field": "month_name", "title": "Month"},
                                  {"field": "records", "title": "Records 2020–24", "format": ","},
                                  {"field": "share_of_year", "title": "% of the year's records", "format": ".1f"},
                                  {"field": "index_vs_avg", "title": "× an average month", "format": ".2f"}]}},
        {"transform": [{"filter": "datum.index_vs_avg >= 2 || datum.index_vs_avg <= 0.4"}],
         "mark": {"type": "text", "fontSize": 10.5, "fontWeight": 600},
         "encoding": {"text": {"field": "index_vs_avg", "format": ".1f"},
                      "color": {"value": "#ffffff"}}},
    ],
})
