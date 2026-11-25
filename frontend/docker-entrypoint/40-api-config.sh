#!/bin/sh
set -eu

api_base_url=${AYPE_API_BASE_URL:-}

if [ -z "$api_base_url" ]; then
    if [ -n "${ECS_CONTAINER_METADATA_URI_V4:-}" ]; then
        echo 'AYPE_API_BASE_URL must be set in ECS; the local fallback is disabled there.' >&2
        exit 1
    fi

    if [ "${ALLOW_LOCAL_API_FALLBACK:-false}" != "true" ]; then
        echo 'Set AYPE_API_BASE_URL or explicitly enable ALLOW_LOCAL_API_FALLBACK=true for local development.' >&2
        exit 1
    fi

    api_base_url=http://127.0.0.1:8000
fi

if ! printf '%s' "$api_base_url" | grep -Eq '^https?://[A-Za-z0-9.-]+(:[0-9]+)?(/[A-Za-z0-9._~/-]*)?$'; then
    echo 'AYPE_API_BASE_URL must be an http(s) URL with an optional port and path.' >&2
    exit 1
fi

printf 'window.AYPE_API_BASE_URL = "%s";\n' "$api_base_url" > /usr/share/nginx/html/config.js
