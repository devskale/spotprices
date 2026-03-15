# Live System Documentation

## System Architecture Overview

The spotprices system consists of three main components:

1. **Data Processing Server (amd)** - Crawls, analyzes, and serves API data
2. **WordPress Site (amd2)** - Displays tariff information to end users
3. **LLM API Server (amd)** - Provides AI inference for tariff analysis

---

## Server 1: AMD (amd1.mooo.com)

### SSH Access
```
Host: amd1.mooo.com
User: ubuntu
SSH Alias: amd
```

### Services Running

| Service | Port | Description |
|---------|------|-------------|
| fastapi.service | 8001 | Main API (Gunicorn + Uvicorn) |
| robotni-api.service | - | ARQ FastAPI Server |
| nginx | 80/443 | Reverse proxy with SSL |

### Directory Structure

```
/home/ubuntu/code/
├── web_apis/                    # Main API application
│   ├── main.py                  # FastAPI app entry point
│   ├── electricity -> ../spotprices/electricity/  # Symlink to electricity module
│   ├── .venv/                   # Python virtual environment
│   └── api.log                  # Access logs
│
├── spotprices/                  # Spot prices project
│   ├── get_tarife.py            # Tariff crawler
│   ├── llm_analyze.py           # LLM analysis
│   ├── gen_chartsvg.py          # Chart generation
│   ├── config.py                # Configuration
│   ├── passwords.json           # API keys (git-ignored)
│   ├── data/
│   │   ├── crawls/              # Crawled tariff data
│   │   │   ├── crawl_*.txt      # Individual crawl files
│   │   │   └── report_*_tab.md  # LLM-generated tariff table
│   │   └── charts/              # Generated SVG charts
│   │       ├── price_chart_YYYY-MM-DD.svg        # Single day
│   │       └── price_chart_YYYY-MM-DD_YYYY-MM-DD.svg  # Week range
│   ├── electricity/             # Electricity API module
│   │   └── api/v1/
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── tarifliste.py
│   │           └── spotprices.py
│   └── strom-tarif-plugin/      # WordPress plugin source
│
└── llmapi/uniinfer/             # LLM inference server (port 8123)
```

### API Endpoints (web_apis)

Base URL: `https://amd1.mooo.com/api/`

| Endpoint | Auth | Description |
|----------|------|-------------|
| `/echo` | Bearer | Echo test |
| `/fetch_url` | Bearer | Web page fetching (w3m/lynx) |
| `/duck/search` | Bearer | DuckDuckGo search |
| `/duck/news` | Bearer | DuckDuckGo news |
| `/pdf/to_md` | Bearer | PDF to Markdown |
| `/electricity/tarifliste` | Bearer | Tariff list (⚠️ currently broken) |
| `/electricity/spotprices/chart/latest` | Bearer | Price charts (⚠️ currently broken) |

### Nginx Configuration

```nginx
# /api/ proxies to FastAPI on port 8001
location /api/ {
    client_max_body_size 100M;
    proxy_pass http://127.0.0.1:8001/;
}
```

### Scheduled Tasks (Crontab)

```cron
# Generate spot price charts (twice daily)
15 14 * * * cd /home/ubuntu/code/spotprices && uv run python gen_chartsvg.py
15 15 * * * cd /home/ubuntu/code/spotprices && uv run python gen_chartsvg.py

# Crawl and analyze tariffs (Fridays at 9:00)
0 9 * * 5 cd /home/ubuntu/code/spotprices && uv run python get_tarife.py && uv run python llm_analyze.py
```

### LLM API (uniinfer)

- **URL**: `https://amd1.mooo.com:8123/v1`
- **Models Available**: tu@mistral-small-3.2-24b, tu@qwen-coder-30b, tu@glm-4.7-355b, groq@moonshotai/kimi-k2-instruct

---

## Server 2: AMD2 (WordPress)

### SSH Access
```
Host: 158.180.42.218
User: ubuntu
SSH Alias: amd2
```

### WordPress Installation

| Property | Value |
|----------|-------|
| Path | `/var/www/gwen.at/` |
| Database | `gwendb` |
| DB User | `gwenadmin` |
| URL | https://gwen.at |

### Active Plugins

| Plugin | Version | Status |
|--------|---------|--------|
| strom-tarif-plugin | 1.0.4 | Active |
| wordpress-seo | 25.5 | Active |
| antispam-bee | 2.11.7 | Active |
| dsgvo-tools-cookie-hinweis-datenschutz | 1.11 | Active |
| wpvivid-backuprestore | 0.9.117 | Active |

### Strom-Tarif-Plugin

**Location**: `/var/www/gwen.at/wp-content/plugins/strom-tarif-plugin/`

**Files**:
- `strom-tarif-plugin.php` - Main plugin file
- `admin.php` - Admin settings page
- `css/style.css` - Styling

**Shortcodes**:
- `[display_strom_tariffs layout="table" rows="10"]` - Display tariff table
- `[display_strom_tariffs layout="cards"]` - Display tariff cards
- `[stromgraph range="singleday"]` - Display price chart (single day)
- `[stromgraph range="range"]` - Display price chart (week range)

**Plugin Settings** (WordPress Admin):
- API URL: `https://amd1.mooo.com/api`
- API Key: Configured in `strom_tarif_api_key` option
- Table rows: Default 10
- Card provider filter: Optional

### API Integration

The WordPress plugin fetches data from:
- **Tariffs**: `https://amd1.mooo.com/api/electricity/tarifliste?rows=N&contentformat=json`
- **Charts**: `https://amd1.mooo.com/api/electricity/spotprices/chart/latest?range=singleday|range`

**Authentication**: Bearer token (stored in WordPress options)

**Caching**: 1 hour transient cache

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA PIPELINE                           │
└─────────────────────────────────────────────────────────────────┘

1. TARIFF DATA COLLECTION (Weekly - Fridays 9:00)
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Google Sheet │────▶│ get_tarife.py│────▶│ data/crawls/ │
   │ (Tarif URLs) │     │   (crawler)  │     │  crawl_*.txt │
   └──────────────┘     └──────────────┘     └──────────────┘
                                                      │
                                                      ▼
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ LLM API      │◀────│llm_analyze.py│◀────│ Crawl files  │
   │ (uniinfer)   │     │              │     │              │
   └──────────────┘     └──────────────┘     └──────────────┘
          │                   │
          ▼                   ▼
   ┌──────────────────────────────────────┐
   │ data/crawls/report_YYYYMMDD_tab.md   │
   │ (Markdown table with tariff data)    │
   └──────────────────────────────────────┘

2. SPOT PRICE CHARTS (Daily - 14:15 & 15:15)
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ Awattar API  │────▶│gen_chartsvg.py│───▶│ data/charts/ │
   │ SmartEnergy  │     │              │     │  *.svg       │
   └──────────────┘     └──────────────┘     └──────────────┘

3. API SERVING (On-demand)
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ FastAPI      │────▶│ tarifliste   │────▶│ WordPress    │
   │ (port 8001)  │     │ endpoint     │     │ (amd2)       │
   └──────────────┘     └──────────────┘     └──────────────┘
          │                   │
          ▼                   ▼
   ┌──────────────┐     ┌──────────────┐
   │ Nginx proxy  │     │ spotprices   │
   │ /api/        │     │ endpoint     │
   └──────────────┘     └──────────────┘

4. WORDPRESS DISPLAY
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ WP Shortcode │────▶│ Plugin PHP   │────▶│ API Request  │
   │ [display_...]│     │              │     │ (cached)     │
   └──────────────┘     └──────────────┘     └──────────────┘
```

---

## Authentication

### API Tokens

| Token Name | Value | Usage |
|------------|-------|-------|
| TOKEN_1 | (see passwords.json) | Development |
| TOKEN_2 | (see passwords.json) | WordPress plugin |
| TOKEN_3 | (see passwords.json) | Secondary |
| strom_tarif_api_key | (from passwords.json) | Electricity API |

### LLM API Keys

Stored in `/home/ubuntu/code/spotprices/passwords.json`:
- `unii_api_key` - uniinfer LLM API
- `jina_bearer` - Jina AI reader

---

## Current Issues

### ⚠️ Electricity API Endpoints Not Loading

**Problem**: The `/electricity/*` endpoints return 404 "Not Found"

**Root Cause**: Module import error in `electricity/api/v1/router.py`:
```python
from config import get_secret  # Fails because config.py is in spotprices/, not web_apis/
```

**Fix Required**: Either:
1. Add `/home/ubuntu/code/spotprices` to Python path in web_apis
2. Or modify the electricity module to use relative imports
3. Or restart the fastapi service after fixing the import

**Verification**:
```bash
ssh amd "systemctl restart fastapi.service"
ssh amd "curl localhost:8001/electricity/tarifliste?rows=1 -H 'Authorization: Bearer YOUR_API_KEY'"
```

---

## Deployment Checklist

### After Code Changes

1. **Push to Git**:
   ```bash
   git push origin main
   ```

2. **Pull on Server**:
   ```bash
   ssh amd "cd /home/ubuntu/code/spotprices && git pull"
   ```

3. **Restart API** (if needed):
   ```bash
   ssh amd "sudo systemctl restart fastapi.service"
   ```

### WordPress Plugin Update

1. **Build Plugin**:
   ```bash
   ./make_plugin_zip.sh
   ```

2. **Deploy to WordPress**:
   ```bash
   scp -r strom-tarif-plugin amd2:/var/www/gwen.at/wp-content/plugins/
   ```

3. **Clear Cache**:
   - WordPress Admin > Settings > Strom Tarif > Clear Cache

---

## Monitoring

### Log Files

| Log | Location | Purpose |
|-----|----------|---------|
| API Access | `/home/ubuntu/code/web_apis/api.log` | API requests |
| Cron Output | `/home/ubuntu/code/spotprices/cron.log` | Chart generation |
| Tariff Cron | `/home/ubuntu/code/spotprices/tarife_cron.log` | Tariff crawling |

### Check Service Status

```bash
ssh amd "systemctl status fastapi.service"
ssh amd "journalctl -u fastapi.service -n 50"
```

### Check Recent Data

```bash
ssh amd "ls -lt /home/ubuntu/code/spotprices/data/crawls/ | head -10"
ssh amd "ls -lt /home/ubuntu/code/spotprices/data/charts/ | head -5"
```

---

## Quick Reference Commands

### Test API Locally
```bash
ssh amd "curl localhost:8001/electricity/tarifliste?rows=3 -H 'Authorization: Bearer YOUR_API_KEY'"
```

### Run Crawler Manually
```bash
ssh amd "cd /home/ubuntu/code/spotprices && uv run python get_tarife.py"
```

### Run LLM Analysis
```bash
ssh amd "cd /home/ubuntu/code/spotprices && uv run python llm_analyze.py --step both"
```

### Generate Charts
```bash
ssh amd "cd /home/ubuntu/code/spotprices && uv run python gen_chartsvg.py"
```

### View Current Report
```bash
ssh amd "cat /home/ubuntu/code/spotprices/data/crawls/report_*_tab.md"
```

---

## Contact & Credits

- **Developer**: dev@gwen.at
- **Organization**: skale.dev
- **Website**: https://gwen.at
