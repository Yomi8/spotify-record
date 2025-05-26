#!/bin/bash
set -e

cd /spotify-record

# Pull latest code
git pull origin main

# Build frontend
cd frontend
npm install
npm run build

# Restart backend (example using systemctl for gunicorn)
sudo systemctl restart spotify-record-backend.service

# Restart Nginx if config changed (optional)
sudo systemctl reload nginx

