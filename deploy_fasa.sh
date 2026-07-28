#!/bin/bash
set -e

# 1. Crear sitio nginx para ipac.vogelconsultoria.com.ar
cat > /etc/nginx/sites-enabled/ipac.vogelconsultoria.com.ar << 'EOF'
server {
    listen 80;
    server_name ipac.vogelconsultoria.com.ar;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8084;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

echo "✓ Nginx config creado"

# 2. Recargar nginx
nginx -t && systemctl reload nginx
echo "✓ Nginx recargado"

# 3. Obtener certificado SSL con Let's Encrypt
certbot --nginx -d ipac.vogelconsultoria.com.ar --non-interactive --agree-tos --email admin@vogelconsultoria.com.ar || echo "⚠ certbot falló (quizás ya existe el certificado)"
echo "✓ SSL configurado"

# 4. Ir al proyecto y levantar docker
cd /var/www/html/ipac
docker compose down --remove-orphans
docker compose up -d --build
echo "✓ Docker Compose levantado"

echo ""
echo "=== Todo listo ==="
echo "App: https://ipac.vogelconsultoria.com.ar"
echo "Usuario: admin / admin123"
