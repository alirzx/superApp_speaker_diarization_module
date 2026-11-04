FROM node:22-alpine AS build
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ .
RUN npm run build

# Alpine nginx's 'nginx' user is UID/GID 101.
# Build-time ownership applies to image paths; the Compose tmpfs mounts
# must ALSO be uid=101/gid=101 because tmpfs hides image ownership.
FROM nginx:1.27-alpine
RUN apk add --no-cache gettext \
    && mkdir -p /var/cache/nginx /var/run /etc/nginx/conf.d \
    && chown -R nginx:nginx /var/cache/nginx /var/run /etc/nginx/conf.d
COPY --from=build /web/dist /usr/share/nginx/html
COPY ops/nginx.conf.template /etc/nginx/nginx.conf.template
COPY ops/start-nginx.sh /start-nginx.sh
RUN chmod 0555 /start-nginx.sh
USER nginx
EXPOSE 8080
ENTRYPOINT ["/start-nginx.sh"]
