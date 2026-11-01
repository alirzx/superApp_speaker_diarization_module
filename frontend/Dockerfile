FROM node:22-alpine AS build
WORKDIR /web
COPY frontend/package*.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ .
RUN npm run build
FROM nginx:1.27-alpine
COPY --from=build /web/dist /usr/share/nginx/html
COPY ops/nginx.conf.template /etc/nginx/templates/default.conf.template
EXPOSE 8080
