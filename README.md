# Urban Wildlife in Australia's Capital Cities

FIT3179 Data Visualisation 2 · Monash University · Semester 2, 2026
Topic 15, *Urban Wildlife*: compare observations of birds, mammals, reptiles and insects across Australian cities to explore how biodiversity changes in urban areas.

By Le Duy Anh Vo

A single scrolling data story with 13 Vega-Lite / Vega visualisations (3 maps), built from two independent sources: the Atlas of Living Australia (wildlife records) and the Australian Bureau of Statistics (population and boundaries).

## Repository layout

| Path | What it is |
|---|---|
| `index.html`, `css/style.css` | The web page (GitHub Pages serves `index.html`). |
| `specs/` | One human-readable JSON specification per chart (`.vl.json` = Vega-Lite, `.vg.json` = Vega). |
| `data/` | The tidy data files the charts load (≈0.7 MB in total). |
| `data-prep/raw/` | The exact extracts retrieved from the ALA and ABS APIs (12 Oct 2026). |
| `data-prep/build_data.py` | Reformats the raw extracts into `data/` (shares, ranks and density are simple arithmetic on the raw counts). |
| `data-prep/make_specs.py` | Generates every file in `specs/` with shared colours, fonts and projection. |
| `data-prep/build.sh` | Rebuilds `data/` and `specs/` from scratch (downloads the ABS boundary files, simplifies them with mapshaper). |
| `data-prep/render_check.mjs` | Renders every spec headlessly to catch errors. |
The hand-drawn sketch (sketch.pdf).

## The 13 visualisations

| # | Chart | Idiom | Advanced? |
|---|---|---|---|
| 1 | Species recorded per capital | **Proportional symbol map** (Albers equal-area) | ✔ map |
| 2 | What each city's species list is made of | **Marimekko** (variable-width stacked) | ✔ |
| 3 | Share of sightings vs share of species | **Waffle charts** (unit charts) | ✔ |
| 4 | Records per year, 2010 - 2024 | Multi-line chart, log scale | basic |
| 5 | Which datasets supply the records | **Treemap** (Vega) | ✔ |
| 6 | Major cities vs very remote Australia | **Slope graph** | ✔ |
| 7a | Species per council area | **Choropleth map** (linked) | ✔ map |
| 7b | Population density vs species | Scatterplot + trend line (linked) | basic |
| 8 | Melbourne's wildlife hotspots | **Gridded density map** (2 km cells) | ✔ map |
| 9 | Birds shared between cities | **Dot matrix** (table heat map) | ✔ |
| 10 | Each city's top five mammals | Small-multiple bar charts | basic |
| 11 | Threatened species per city | Stacked bar chart | basic |
| 12 | Seasonal rhythm by group | **Radial / rose charts** (small multiples) | ✔ |
| 13 | Month × city seasonality | **Heat map** (diverging, log) | ✔ |

Distinct advanced idioms: 10 (three of them maps). Interactivity: group and city dropdowns, a choropleth ↔ scatterplot hover link, legend-click highlighting, hover isolation on the slope graph, a treemap scale toggle and tooltips on every mark.

## Data sources

1. **Atlas of Living Australia** — occurrence records, biocache web service (`https://biocache-ws.ala.org.au/ws/`), accessed 12 Oct 2026. Filters: classes Aves, Mammalia, Reptilia, Insecta; years 2020–2024 (2010–2024 for the trend chart); `occurrenceStatus:PRESENT`; `spatiallyValid:true`. Counts are facet totals by the ALA's ABS Greater Capital City Statistical Area 2021 (`cl11166`), Local Government Area 2023 (`cl11170`), Remoteness Area 2016 (`cl10936`) and 0.02° grid (`point-0.02`) fields. Species counts are distinct values of the `species` field. Threatened = records carrying an EPBC status (`countryConservation`). Records are contributed by many datasets (eBird Australia, iNaturalist Australia, BirdLife Australia Birdata, NSW BioNet and others) under their own licences.
2. **Australian Bureau of Statistics** — Estimated Resident Population, 30 June 2025, ABS Data API (`https://data.api.abs.gov.au/`), dataflows `ERP_LGA2025` and `ABS_ANNUAL_ERP_ASGS2021`. CC BY 4.0.
3. **ABS digital boundaries** (ASGS Edition 3: states and territories; LGA 2022) as distributed by geoBoundaries (`https://www.geoboundaries.org`, gbOpen AUS ADM1/ADM2). CC BY 4.0.

