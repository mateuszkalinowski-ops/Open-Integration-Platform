FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN if [ -f package-lock.json ]; then npm ci --ignore-scripts; else npm install --ignore-scripts; fi
COPY . .
RUN npx ng build integrations-lib --configuration=production
RUN npx ng build dashboard-app --configuration=production

FROM nginx:alpine
LABEL maintainer="integrations@pinquark.com"
LABEL component="dashboard"
COPY --from=build /app/dist/dashboard-app/browser /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh
EXPOSE 80
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:80/ || exit 1
ENTRYPOINT ["/docker-entrypoint.sh"]
