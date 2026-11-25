FROM nginx:1.27-alpine

COPY site/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --chmod=755 docker-entrypoint/40-api-config.sh /docker-entrypoint.d/40-api-config.sh

EXPOSE 80