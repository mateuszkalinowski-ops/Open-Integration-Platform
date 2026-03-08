#!/bin/sh
mkdir -p /usr/share/nginx/html/assets
cat > /usr/share/nginx/html/assets/runtime-config.js <<EOF
window.__PINQUARK_CONFIG__ = {
  apiUrl: '${PINQUARK_API_URL:-}',
  apiKey: '${PINQUARK_API_KEY:-}',
  adminSecret: '${PINQUARK_ADMIN_SECRET:-}'
};
EOF

CACHE_BUST=$(date +%s)
sed -i "s|assets/runtime-config.js[^\"]*|assets/runtime-config.js?v=${CACHE_BUST}|g" /usr/share/nginx/html/index.html

exec nginx -g 'daemon off;'
