#!/usr/bin/env bash
set -euo pipefail

# Usage: sudo ./scripts/init-ssl.sh <domain> <email>
# Example: sudo ./scripts/init-ssl.sh lpquant.example.com admin@example.com

DOMAIN="${1:?Usage: $0 <domain> <email>}"
EMAIL="${2:?Usage: $0 <domain> <email>}"

echo "==> Initializing SSL for ${DOMAIN}..."

# Step 1: Replace domain placeholder in nginx config
sed -i "s/__DOMAIN__/${DOMAIN}/g" nginx/conf.d/default.conf
echo "==> Updated nginx config with domain: ${DOMAIN}"

# Step 2: Start services with HTTP-only config
echo "==> Starting services..."
docker compose up -d nginx web quant
echo "==> Waiting for services to be ready..."
sleep 10

# Step 3: Obtain certificate
echo "==> Requesting Let's Encrypt certificate..."
docker compose run --rm certbot certonly \
  --webroot \
  -w /var/www/certbot \
  -d "${DOMAIN}" \
  --email "${EMAIL}" \
  --agree-tos \
  --no-eff-email \
  --force-renewal

# Step 4: Write HTTPS config
echo "==> Writing HTTPS nginx config..."
cat > nginx/conf.d/default.conf <<NGINX_EOF
# HTTP -> HTTPS redirect
server {
    listen 80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl;
    http2 on;
    server_name ${DOMAIN};

    ssl_certificate /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;

    # SSL settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header Referrer-Policy strict-origin-when-cross-origin always;

    # Static assets caching
    location /_next/static/ {
        proxy_pass http://nextjs;
        proxy_cache_valid 200 365d;
        add_header Cache-Control "public, max-age=31536000, immutable";
    }

    location / {
        proxy_pass http://nextjs;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
}
NGINX_EOF

# Step 5: Reload nginx with HTTPS config
echo "==> Reloading nginx with HTTPS config..."
docker compose exec nginx nginx -s reload

# Step 6: Start certbot renewal service
echo "==> Starting certbot auto-renewal..."
docker compose up -d certbot

echo ""
echo "==> SSL setup complete!"
echo "==> Your site is now available at: https://${DOMAIN}"
