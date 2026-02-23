#!/bin/sh
mkdir -p /usr/share/nginx/html/assets
cat > /usr/share/nginx/html/assets/runtime-config.js <<EOF
window.__PINQUARK_CONFIG__ = {
  apiUrl: '${PINQUARK_API_URL:-}',
  apiKey: '${PINQUARK_API_KEY:-}'
};
EOF

exec nginx -g 'daemon off;'
