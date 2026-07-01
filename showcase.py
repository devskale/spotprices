"""Showcase server — serves a single HTML page that fetches REAL data from
the main API (port 8000) and renders the tariff table + spot-price charts
side by side. No mocks, no fixtures — just a viewer for the live E2E output.

Run:
    uv run --group dev uvicorn showcase:app --port 8899 --reload
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Spotprices Showcase", docs_url=None, redoc_url=None)

API_BASE = "http://localhost:8000"

SHOWCASE_HTML = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Spotprices Showcase</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
         background: #f8fafc; color: #1f2937; padding: 20px; }}
  h1 {{ font-size: 24px; margin-bottom: 4px; }}
  .subtitle {{ color: #6b7280; margin-bottom: 24px; font-size: 14px; }}
  .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .section h2 {{ font-size: 18px; margin-bottom: 16px; }}
  .charts {{ display: grid; gap: 24px; }}
  .chart-wrap {{ background: #fafafa; border-radius: 8px; padding: 12px; }}
  .chart-wrap h3 {{ font-size: 14px; color: #6b7280; margin-bottom: 8px; font-weight: 500; }}
  .chart-svg-wrap {{ max-width: 700px; margin: 0 auto; }}
  .chart-svg {{ width: 100%; height: auto; display: block; }}
  /* Non-scaling text: SVG text normally scales with the viewBox, making it
     tiny on phones. This counteracts the scale so text stays a fixed px size.
     --text-factor is set by JS (ResizeObserver) = viewBox_width / rendered_width.
     Text is hidden until the factor is set, to avoid a flash of wrong-size text. */
  .chart-svg text {{
    font-size: calc(13px * var(--text-factor, 0));
  }}
  .chart-svg .chart-title {{
    font-size: calc(16px * var(--text-factor, 0));
  }}
  .chart-svg.loaded text {{ visibility: visible; }}
  /* On small screens the fixed-size text collides. Hide secondary labels
     progressively so the remaining ones have room. */
  @media (max-width: 600px) {{
    .chart-svg .day-date {{ display: none; }}
    .chart-svg .legend {{ display: none; }}
  }}
  @media (max-width: 450px) {{
    .chart-svg .day-label {{ display: none; }}
    .chart-svg .axis-label {{ font-size: calc(11px * var(--text-factor, 0)); }}
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ text-align: left; padding: 10px 8px; border-bottom: 2px solid #e5e7eb;
       font-weight: 600; color: #374151; white-space: nowrap; }}
  td {{ padding: 10px 8px; border-bottom: 1px solid #f3f4f6; vertical-align: top; }}
  tr:hover {{ background: #f9fafb; }}
  .provider {{ font-weight: 600; }}
  .tarifname a {{ color: #2563eb; text-decoration: none; }}
  .tarifname a:hover {{ text-decoration: underline; }}
  .price {{ font-weight: 600; white-space: nowrap; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px;
            font-size: 11px; font-weight: 500; }}
  .badge-bezug {{ background: #dbeafe; color: #1e40af; }}
  .badge-einspeisung {{ background: #dcfce7; color: #166534; }}
  .meta {{ color: #9ca3af; font-size: 12px; margin-bottom: 12px; }}
  .error {{ color: #ef4444; padding: 16px; }}
  .loading {{ color: #6b7280; padding: 20px; text-align: center; }}
  .controls {{ margin-bottom: 16px; }}
  .controls button {{ padding: 6px 14px; margin-right: 8px; border: 1px solid #d1d5db;
       border-radius: 6px; background: white; cursor: pointer; font-size: 13px; }}
  .controls button.active {{ background: #1f2937; color: white; border-color: #1f2937; }}
</style>
</head>
<body>
  <h1>Strom-Spotpreise &amp; Tarife</h1>
  <p class="subtitle">Live showcase — real data from the spotprices API (port 8000)</p>

  <div class="section">
    <h2>Spotpreis-Charts (EPEX AT)</h2>
    <div class="charts">
      <div class="chart-wrap">
        <h3>Heute</h3>
        <div class="chart-svg-wrap"><div id="chart-day" class="loading">Lade Chart...</div></div>
      </div>
      <div class="chart-wrap">
        <h3>Woche</h3>
        <div class="chart-svg-wrap"><div id="chart-week" class="loading">Lade Chart...</div></div>
      </div>
    </div>
  </div>

  <div class="section">
    <h2>Tariftabelle</h2>
    <div class="controls">
      <button onclick="filterTable('')" class="active" id="btn-all">Alle</button>
      <button onclick="filterTable('Bezug')" id="btn-bezug">Bezug</button>
      <button onclick="filterTable('Einspeisung')" id="btn-einspeisung">Einspeisung</button>
    </div>
    <p class="meta" id="tariff-meta">Lade Tarife...</p>
    <div style="overflow-x:auto;">
      <table id="tariff-table">
        <thead>
          <tr>
            <th>Anbieter</th>
            <th>Tarif</th>
            <th>Art</th>
            <th>Preisanpassung</th>
            <th>Strompreis</th>
            <th>Beschreibung</th>
          </tr>
        </thead>
        <tbody id="tariff-body">
          <tr><td colspan="6" class="loading">Lade Tarife...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

<script>
const API = "{API_BASE}";
let allTariffs = [];

// Load charts — fetch SVG as text and inline it so CSS can control font sizes
// independently of the chart scaling (text stays readable on small screens)
function inlineChart(url, elementId) {{
  fetch(url)
    .then(r => r.text())
    .then(svg => {{
      const el = document.getElementById(elementId);
      el.innerHTML = svg;
      const svgEl = el.querySelector('svg');
      svgEl.classList.add('chart-svg');
      // strip any fixed width/height so it fills the container
      svgEl.removeAttribute('width');
      svgEl.removeAttribute('height');
      // Non-scaling text: counteract SVG scaling so text stays a fixed px size.
      // Based on https://muffinman.io/blog/preserving-text-size-when-scaling-svgs/
      const viewBox = svgEl.getAttribute('viewBox');
      if (viewBox) {{
        const naturalWidth = parseFloat(viewBox.split(' ')[2]);
        const updateFactor = () => {{
          const factor = naturalWidth / svgEl.clientWidth;
          svgEl.style.setProperty('--text-factor', factor);
          svgEl.classList.add('loaded');
        }};
        updateFactor();
        new ResizeObserver(updateFactor).observe(svgEl);
      }} else {{
        svgEl.classList.add('loaded');
      }}
    }})
    .catch(err => {{
      document.getElementById(elementId).innerHTML =
        '<span class="error">Chart-Fehler: ' + err + '</span>';
    }});
}}
inlineChart(API + '/electricity/spotprices/chart/latest?range=singleday&t=' + Date.now(), 'chart-day');
inlineChart(API + '/electricity/spotprices/chart/latest?range=range&t=' + Date.now(), 'chart-week');

// Load tariffs
fetch(API + "/electricity/tarifliste?rows=100")
  .then(r => r.json())
  .then(data => {{
    allTariffs = data.tariffs || [];
    const meta = data.metadata || {{}};
    document.getElementById('tariff-meta').textContent =
      allTariffs.length + ' Tarife — Stand: ' + (meta.report_date || 'unbekannt');
    renderTable('');
  }})
  .catch(err => {{
    document.getElementById('tariff-body').innerHTML =
      '<tr><td colspan="6" class="error">Fehler beim Laden: ' + err + '</td></tr>';
  }});

function renderTable(filter) {{
  const tbody = document.getElementById('tariff-body');
  const tariffs = filter ? allTariffs.filter(t => t.tarifart.includes(filter)) : allTariffs;
  if (!tariffs.length) {{
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Keine Tarife</td></tr>';
    return;
  }}
  tbody.innerHTML = tariffs.map(t => {{
    const badge = t.tarifart.includes('Einspeisung') ? 'badge-einspeisung' : 'badge-bezug';
    const name = t.tarifname || '';
    const link = t.link && t.link !== '-' ? `<a href="${{t.link}}" target="_blank">${{escapeHtml(name)}}</a>` : escapeHtml(name);
    return `<tr>
      <td class="provider">${{escapeHtml(t.stromanbieter)}}</td>
      <td class="tarifname">${{link}}</td>
      <td><span class="badge ${{badge}}">${{escapeHtml(t.tarifart)}}</span></td>
      <td>${{escapeHtml(t.preisanpassung)}}</td>
      <td class="price">${{escapeHtml(t.strompreis)}}</td>
      <td>${{escapeHtml(t.kurzbeschreibung)}}</td>
    </tr>`;
  }}).join('');
}}

function filterTable(filter) {{
  renderTable(filter);
  document.querySelectorAll('.controls button').forEach(b => b.classList.remove('active'));
  const id = filter === '' ? 'btn-all' : (filter === 'Bezug' ? 'btn-bezug' : 'btn-einspeisung');
  document.getElementById(id).classList.add('active');
}}

function escapeHtml(s) {{
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def showcase():
    return SHOWCASE_HTML
