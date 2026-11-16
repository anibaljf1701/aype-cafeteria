#!/bin/sh
set -eu

api_base_url=${AYPE_API_BASE_URL:-http://127.0.0.1:8000}

if ! printf '%s' "$api_base_url" | grep -Eq '^https?://[A-Za-z0-9.-]+(:[0-9]+)?(/[A-Za-z0-9._~/-]*)?$'; then
    echo 'AYPE_API_BASE_URL must be an http(s) URL with an optional port and path.' >&2
    exit 1
fi

printf 'window.AYPE_API_BASE_URL = "%s";\n' "$api_base_url" > /usr/share/nginx/html/config.js
