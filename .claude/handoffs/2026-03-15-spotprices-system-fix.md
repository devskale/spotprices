# Spotprices System Verification and Fix

## Handoff Purpose
Continue work on verifying and fixing the spotprices system on live servers amd and amd2.

## 1. Primary Request and Intent
The user requested verification of the complete spotprices system:
- **Crawl functionality**: Verify `get_tarife.py` works to crawl tariff data
- **LLM analysis**: Verify `llm_analyze.py` processes crawled data
- **API**: Verify the FastAPI endpoints on `amd` serve tariff and chart data
- **WordPress Plugin**: Verify the strom-tarif-plugin on `amd2` displays data correctly

## 2. Key Technical Concepts
- **FastAPI with Gunicorn/Uvicorn**: API served on port 8001, proxied via nginx
- **Systemd service management**: `fastapi.service` runs the API
- **Python environment**: Using `uv` package manager, virtual environments
- **WordPress plugin architecture**: Shortcodes `[display_strom_tariffs]`, `[stromgraph]`
- **Bearer token authentication**: API requires `Authorization: Bearer Gw3nAt23Elec`
- **LLM integration**: uniinfer server at port 8123 for tariff analysis
- **Cron-based automation**: Charts generated twice daily, tariffs crawled weekly

## 3. Files and Code Sections

### `/home/ubuntu/code/spotprices/electricity/api/v1/router.py` (amd)
- **Why important**: Core router for electricity API endpoints, was broken due to import issue
- **Changes made**: Fixed import to use environment variable instead of config module
- **Code snippet**:
```python
# electricity/api/v1/router.py
from typing import Optional
import os

from fastapi import APIRouter, Depends, Header, HTTPException

from .endpoints import tarifliste, spotprices


def get_strom_tarif_api_key() -> str:
    """Get API key from environment variable (works in both contexts)."""
    return os.environ.get("STROM_TARIF_API_KEY", "")


def require_bearer_auth(authorization: Optional[str] = Header(default=None)) -> None:
    expected = get_strom_tarif_api_key()
    if not expected:
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(status_code=403, detail="Invalid bearer token")


router = APIRouter()

router.include_router(tarifliste.router, dependencies=[Depends(require_bearer_auth)])
router.include_router(spotprices.router, dependencies=[Depends(require_bearer_auth)])
```

### `/etc/systemd/system/fastapi.service` (amd)
- **Why important**: Needs `STROM_TARIF_API_KEY` environment variable for authentication
- **Changes needed**: Add `Environment="STROM_TARIF_API_KEY=Gw3nAt23Elec"`

### `/home/ubuntu/code/web_apis/main.py` (amd)
- **Why important**: Main FastAPI app that dynamically loads electricity module
- Loads electricity router via symlink: `electricity -> /home/ubuntu/code/spotprices/electricity`

### `/var/www/gwen.at/wp-content/plugins/strom-tarif-plugin/strom-tarif-plugin.php` (amd2)
- **Why important**: WordPress plugin that fetches and displays tariff data
- **Current issue**: Server has v1.0.4, updated v1.0.5 ready at `/home/ubuntu/strom-tarif-plugin/`
- **Endpoints used**:
  - `https://amd1.mooo.com/api/electricity/tarifliste?rows=N&contentformat=json`
  - `https://amd1.mooo.com/api/electricity/spotprices/chart/latest?range=singleday|range`

### `/home/ubuntu/code/spotprices/data/crawls/report_20260313_tab.md` (amd)
- **Why important**: Latest LLM-generated tariff table served by API
- Contains 3 energieAG tariffs in markdown table format

## 4. Problem Solving

### Solved
- **API 404 Error**: Root cause was module import failure. Fixed by changing `from config import get_secret` to `os.environ.get("STROM_TARIF_API_KEY")`.
- **API Endpoints Now Load**: Verified via `curl localhost:8001/openapi.json | jq '.paths | keys'` - shows `/electricity/tarifliste` and `/electricity/spotprices/chart/latest`

### Ongoing
- **Systemd Service Update**: Needs sudo to add environment variable and restart
- **WordPress Plugin Deployment**: Needs sudo to copy from `/home/ubuntu/strom-tarif-plugin/` to `/var/www/gwen.at/wp-content/plugins/strom-tarif-plugin/`

## 5. Pending Tasks

### On amd (requires sudo):
```bash
sudo tee /etc/systemd/system/fastapi.service > /dev/null << 'EOF'
[Unit]
Description=Gunicorn instance to serve FastAPI app
After=network.target

[Service]
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/code/web_apis
Environment="PATH=/home/ubuntu/code/web_apis/.venv/bin"
Environment="STROM_TARIF_API_KEY=Gw3nAt23Elec"
ExecStart=/home/ubuntu/code/web_apis/.venv/bin/gunicorn -w 1 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8001 --timeout 120

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart fastapi.service
```

### On amd2 (requires sudo):
```bash
sudo rsync -avz /home/ubuntu/strom-tarif-plugin/ /var/www/gwen.at/wp-content/plugins/strom-tarif-plugin/
sudo chown -R www-data:www-data /var/www/gwen.at/wp-content/plugins/strom-tarif-plugin/
```

## 6. Verification Commands

### Test API (amd):
```bash
curl -s localhost:8001/electricity/tarifliste?rows=2 -H "Authorization: Bearer Gw3nAt23Elec"
curl -s "localhost:8001/electricity/spotprices/chart/latest?range=singleday" -H "Authorization: Bearer Gw3nAt23Elec" | head -3
```

### Test WordPress (amd2):
```bash
curl -s "https://amd1.mooo.com/api/electricity/tarifliste?rows=2" -H "Authorization: Bearer Gw3nAt23Elec"
wp option list --path=/var/www/gwen.at --search='strom_*'
```

## 7. Server Access

| Server | SSH Alias | IP | Role |
|--------|-----------|-----|------|
| amd | `ssh amd` | amd1.mooo.com | API server, data processing |
| amd2 | `ssh amd2` | 158.180.42.218 | WordPress (gwen.at) |

## 8. Key API Credentials

| Token | Value | Usage |
|-------|-------|-------|
| STROM_TARIF_API_KEY | Gw3nAt23Elec | Electricity API auth |
| TOKEN_2 | Gw3nAt23Elec | WordPress plugin |

## 9. Directory Structure (amd)

```
/home/ubuntu/code/
├── web_apis/                    # Main API application
│   ├── main.py                  # FastAPI app entry point
│   ├── electricity -> ../spotprices/electricity/  # Symlink
│   └── .venv/                   # Python virtual environment
│
├── spotprices/                  # Spot prices project
│   ├── get_tarife.py            # Tariff crawler
│   ├── llm_analyze.py           # LLM analysis
│   ├── gen_chartsvg.py          # Chart generation
│   ├── data/
│   │   ├── crawls/              # Crawled tariff data
│   │   │   └── report_*_tab.md  # LLM-generated tariff table
│   │   └── charts/              # Generated SVG charts
│   └── electricity/api/v1/      # API endpoints
│       └── endpoints/
│           ├── tarifliste.py
│           └── spotprices.py
```

## 10. Directory Structure (amd2)

```
/var/www/gwen.at/
├── wp-content/plugins/strom-tarif-plugin/
│   ├── strom-tarif-plugin.php   # Main plugin file
│   ├── admin.php                # Admin settings
│   └── css/style.css
```

## 11. Crontab (amd)

```cron
# Generate spot price charts (twice daily)
15 14 * * * cd /home/ubuntu/code/spotprices && uv run python gen_chartsvg.py
15 15 * * * cd /home/ubuntu/code/spotprices && uv run python gen_chartsvg.py

# Crawl and analyze tariffs (Fridays at 9:00)
0 9 * * 5 cd /home/ubuntu/code/spotprices && uv run python get_tarife.py && uv run python llm_analyze.py
```
