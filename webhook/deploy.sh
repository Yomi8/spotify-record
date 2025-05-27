#!/bin/bash
set -e

export PATH=$PATH:/usr/bin:/bin

cd /spotify-record

# Pull latest code
/usr/bin/git pull

# Build frontend
cd frontend
npm install
npm run build

# Restart backend (example using systemctl for gunicorn)
sudo systemctl restart backend.service

# Restart Nginx if config changed (optional)
sudo systemctl reload nginx

