#!/usr/bin/env bash
# Rebuild everything in data/ and specs/ from the raw extracts in data-prep/raw.
# Requirements: python3 with shapely + pyproj; node with mapshaper (npx downloads it).
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p geo

GB=https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/AUS
[ -f geo/geoBoundaries-AUS-ADM1_simplified.geojson ] || curl -sSL -o geo/geoBoundaries-AUS-ADM1_simplified.geojson "$GB/ADM1/geoBoundaries-AUS-ADM1_simplified.geojson"
[ -f geo/geoBoundaries-AUS-ADM2_simplified.geojson ] || curl -sSL -o geo/geoBoundaries-AUS-ADM2_simplified.geojson "$GB/ADM2/geoBoundaries-AUS-ADM2_simplified.geojson"

# 1. tidy CSV / JSON files for the charts (+ full-resolution boundary subsets in geo/)
python3 build_data.py

# 2. simplify the boundaries for the web (TopoJSON)
npx -y mapshaper@0.6 geo/states_full.geojson -rename-layers aus_states -simplify 1.5% keep-shapes \
  -filter-islands min-area=200km2 -o format=topojson quantization=1e5 ../data/aus_states.topo.json
npx -y mapshaper@0.6 geo/capital_lgas_full.geojson -rename-layers lgas -simplify 12% keep-shapes \
  -o format=topojson quantization=1e5 ../data/capital_lgas.topo.json

# 3. the Vega-Lite / Vega specifications
python3 make_specs.py
echo "Done. Open ../index.html through a local web server, e.g.  python3 -m http.server  (from the repository root)."
