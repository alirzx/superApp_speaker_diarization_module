#!/bin/sh
set -eu
: "${APP_ENV:=development}"
: "${API_TOKEN:=}"
if [ "$APP_ENV" = production ] && [ "${#API_TOKEN}" -lt 32 ]; then
  echo 'Production UI requires API_TOKEN >= 32 characters' >&2
  exit 1
fi
case "$API_TOKEN" in
  *[!a-zA-Z0-9_-]*)
    echo 'API_TOKEN must contain only letters, digits, underscore or hyphen' >&2
    exit 1
    ;;
esac
# tmpfs /tmp belongs to nginx UID 101; the root filesystem stays read-only.
umask 077
envsubst '${API_TOKEN}' < /etc/nginx/nginx.conf.template > /tmp/nginx.conf
nginx -t -c /tmp/nginx.conf
exec nginx -c /tmp/nginx.conf -g 'daemon off;'
