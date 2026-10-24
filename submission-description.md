# Submission description — Urban Wildlife (FIT3179 Data Visualisation 2)

**Visualisation URL:** https://leduyanhvo.github.io/UrbanWildlifeDV2/
**Sketch (PDF):** https://github.com/LeDuyAnhVo/UrbanWildlifeDV2/blob/main/sketch/sketch.pdf

## i. Domain, why and who

**Domain.** Urban ecology: the wildlife that lives in Australia's eight capital cities (Greater Capital City Statistical Areas), compared across four animal groups — birds, mammals, reptiles and insects.

**Why.** Most Australians live in cities and meet wildlife every day, but they rarely see how much biodiversity a city holds, how it differs between cities, or how it thins out as suburbs get more crowded. The visualisation answers four questions: (1) How many species live in each capital, and what are they? (2) Which animals do we notice, and which do we overlook? (3) How does biodiversity change from the bush to the city, and from leafy to crowded suburbs? (4) When during the year does urban wildlife appear? It ends with a call to action: protect green and blue space, and contribute sightings through citizen-science apps.

**Who.** The average Australian (Clayton campus). Jargon is avoided; the four terms the story needs (record, species recorded, threatened species, log scale) are defined in a short glossary at the top, and every chart has a plain-language headline that states its finding.

## ii. What — the data

| Source | Author / publisher | What it provides | Relevance |
|---|---|---|---|
| Atlas of Living Australia, occurrence records (biocache web service), accessed 12 Oct 2026 | ALA (CSIRO-hosted national biodiversity infrastructure), aggregating eBird Australia, iNaturalist Australia, BirdLife Australia Birdata, state wildlife atlases and others | Counts of wildlife records and of distinct species, 2020–2024, for each capital, each council area (LGA), each ABS remoteness class, each month, each year (2010–2024), each contributing dataset, and a 0.02° grid over Melbourne; top-10 species per city and group; EPBC threatened-species counts | The core evidence of which animals are seen where and when |
| Estimated Resident Population, 30 June 2025 (ABS Data API) | Australian Bureau of Statistics | Population of each capital and each LGA | Turns wildlife counts into a comparison against how crowded an area is (population density) |
| ASGS Edition 3 digital boundaries (states; LGA 2022) via geoBoundaries | ABS (redistributed by geoBoundaries, William & Mary) | Map geometry and LGA areas | Needed for the three maps and for density = population ÷ area |

**Creation process.** Aggregated counts were requested from the ALA and ABS APIs with fixed filters (present, spatially valid records; classes Aves, Mammalia, Reptilia, Insecta; 2020–2024 so that every major dataset's uploads are complete). The raw responses are saved unchanged in `data-prep/raw/` and verified with record-count checksums. A short Python script reformats them into tidy CSV files; the only derived values are shares, ranks, a per-month index (month ÷ average month) and population density. Boundaries were simplified with mapshaper to keep the whole page under 1 MB of data. No values were estimated or edited.

**Caveats shown on the page.** Records measure observer effort as well as wildlife; the story therefore compares species counts where possible, explains the eBird/iNaturalist effect, leaves out 2025 because that year is not complete yet, and notes that crowded LGAs are also smaller.

## iii. How — idioms and rationale

| # | Idiom | Task it supports | Marks and channels |
|---|---|---|---|
| 1 | Proportional symbol map (equal-area Albers, parallels 18°S/36°S) | Compare species totals between cities in their real locations | Point marks; area = species; position = city; dropdown filters the animal group |
| 2 | Marimekko chart | See both how many species each city has and what share each group makes up | Rect marks; width = species total, height = share, colour hue = group |
| 3 | Paired waffle charts | Contrast share of sightings with share of species (91 % birds vs 91 % insects) | 100 unit squares; colour hue = group; count of squares = percentage |
| 4 | Multi-line chart (log scale) | Compare growth rates of records over time | Line marks; slope on log scale = growth rate; legend click highlights a group
| 5 | Treemap (Vega) | Part-to-whole of the datasets behind the records | Nested rect area = records (toggle true / square-root area); hue = group |
| 6 | Slope graph | Compare species counts in major cities vs very remote areas for each group | Line slope = change; log position; direct labels with multipliers |
| 7 | Choropleth map linked to a scatterplot | Find council areas with more or fewer species, then test the pattern against population density | Area colour (single-hue sequential) = species; scatter x = density (log), y = species; shared city/group dropdowns and a two-way hover highlight |
| 8 | Gridded density map | Locate wildlife hotspots within one city | 2 km cells; colour (sequential, log) = records; annotations name two hotspots |
| 9 | Dot matrix | Which birds are shared between cities and how highly ranked | Circle size = share of city's bird records; label = rank |
| 10 | Small-multiple bar charts | Compare each city's top mammals, native vs introduced | Bar length = records; colour = native / introduced |
| 11 | Stacked bar chart | Compare threatened species between cities | Bar length = species; hue = group; sorted |
| 12 | Radial (rose) small multiples | Show the yearly cycle for each group in one city | Wedge angle = month (Jan at top, clockwise); square-root radius = index vs average month; dashed ring = average |
| 13 | Heat map | Compare the seasonal cycle across cities from north to south | Colour (diverging, centred on 1, log) = index vs average month; dropdown selects the group |

**Special features.** The Marimekko layout, the waffle grids, the rose charts (explicit angle encoding) and the linked choropleth/scatter (a shared selection across concatenated views) are custom-built with Vega-Lite transforms; the treemap uses Vega. All maps share one equal-area projection appropriate for Australia. One validated, colour-blind-safe categorical palette encodes the four animal groups consistently across all charts and the text. Typography pairs Bricolage Grotesque (headings) with Source Sans 3 (body and charts).

**Use of generative AI.** Claude (Anthropic) assisted with data retrieval, scripting, Vega-Lite specifications and drafting/proof-reading text; all figures were checked against the source extracts.
