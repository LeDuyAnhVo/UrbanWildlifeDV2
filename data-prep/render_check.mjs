// Usage: npm install vega@5 vega-lite@5 canvas && node data-prep/render_check.mjs <output-folder>\n// Render every spec to SVG with the real data (headless) to catch spec errors before publishing.
import fs from 'fs'; import path from 'path';
import * as vega from 'vega'; import * as vl from 'vega-lite';
const site = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..'); const out = process.argv[2] || '.';
const loader = vega.loader({ baseURL: site + '/', mode: 'file' });
for (const f of fs.readdirSync(site + '/specs').sort()) {
  const spec = JSON.parse(fs.readFileSync(site + '/specs/' + f));
  try {
    const vg = f.endsWith('.vl.json') ? vl.compile(spec).spec : spec;
    const view = new vega.View(vega.parse(vg), { loader, renderer: 'none' });
    const svg = await view.toSVG(); if (process.env.PNG) { const c = await view.toCanvas(1.5); fs.writeFileSync(path.join(out, f.replace(/\.json$/, '.png')), c.toBuffer()); }
    fs.writeFileSync(path.join(out, f.replace(/\.json$/, '.svg')), svg);
    const warn = []; 
    console.log('OK  ', f, svg.length);
  } catch (e) { console.log('FAIL', f, e.message); }
}
