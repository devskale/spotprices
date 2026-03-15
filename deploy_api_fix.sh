#!/bin/bash
# Deploy script to fix electricity API endpoints
# Run this on the amd server with sudo

set -e

echo "=== Fixing Electricity API Endpoints ==="

# 1. Pull latest code
echo "1. Pulling latest code..."
cd /home/ubuntu/code/spotprices
git pull

# 2. Update systemd service to include STROM_TARIF_API_KEY
echo "2. Updating systemd service..."
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

# 3. Reload systemd and restart service
echo "3. Reloading systemd and restarting service..."
sudo systemctl daemon-reload
sudo systemctl restart fastapi.service

# 4. Wait for service to start
sleep 2

# 5. Verify
echo "4. Verifying API..."
curl -s localhost:8001/electricity/tarifliste?rows=1 -H "Authorization: Bearer Gw3nAt23Elec" | head -100

echo ""
echo "=== Done ==="
echo "Check status: sudo systemctl status fastapi.service"
