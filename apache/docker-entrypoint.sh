#!/bin/sh
set -eu

js_escape() {
  printf '%s' "${1:-}" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

js_bool() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) printf 'true' ;;
    0|false|FALSE|no|NO|off|OFF) printf 'false' ;;
    *) printf 'false' ;;
  esac
}

js_int() {
  value="${1:-}"
  default="${2}"

  case "$value" in
    '')
      printf '%s' "$default"
      ;;
    *[!0-9]*)
      printf '%s' "$default"
      ;;
    *)
      printf '%s' "$value"
      ;;
  esac
}

js_array_from_csv() {
  csv="${1:-}"

  if [ -z "$csv" ]; then
    csv="/api/"
  fi

  old_ifs=$IFS
  IFS=','
  set -- $csv
  IFS=$old_ifs

  first=true
  printf '['
  for item in "$@"; do
    trimmed=$(printf '%s' "$item" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
    if [ -z "$trimmed" ]; then
      continue
    fi

    if [ "$first" = true ]; then
      first=false
    else
      printf ', '
    fi

    printf '"%s"' "$(js_escape "$trimmed")"
  done

  if [ "$first" = true ]; then
    printf '"/api/"'
  fi

  printf ']'
}

js_sdk_url_from_site() {
  site=$(printf '%s' "${1:-}" | tr '[:upper:]' '[:lower:]')

  case "$site" in
    datadoghq.com)
      site_path="us1"
      ;;
    us3.datadoghq.com)
      site_path="us3"
      ;;
    us5.datadoghq.com)
      site_path="us5"
      ;;
    datadoghq.eu)
      site_path="eu"
      ;;
    ap1.datadoghq.com)
      site_path="ap1"
      ;;
    ap2.datadoghq.com)
      site_path="ap2"
      ;;
    ddog-gov.com)
      site_path="us1-fed"
      ;;
    *)
      site_path="us1"
      ;;
  esac

  printf 'https://www.datadoghq-browser-agent.com/%s/v6/datadog-rum.js' "$site_path"
}

cat > /usr/local/apache2/htdocs/config.js <<EOF
window.APP_CONFIG = {
  ddRum: {
    applicationId: "$(js_escape "${DD_RUM_APPLICATION_ID:-}")",
    clientToken: "$(js_escape "${DD_RUM_CLIENT_TOKEN:-}")",
    site: "$(js_escape "${DD_RUM_SITE:-}")",
    sdkUrl: "$(js_sdk_url_from_site "${DD_RUM_SITE:-}")",
    service: "$(js_escape "${DD_RUM_SERVICE:-}")",
    env: "$(js_escape "${DD_RUM_ENV:-}")",
    version: "$(js_escape "${DD_RUM_VERSION:-}")",
    sessionSampleRate: $(js_int "${DD_RUM_SESSION_SAMPLE_RATE:-}" "100"),
    sessionReplaySampleRate: $(js_int "${DD_RUM_SESSION_REPLAY_SAMPLE_RATE:-}" "20"),
    trackResources: $(js_bool "${DD_RUM_TRACK_RESOURCES:-true}"),
    trackUserInteractions: $(js_bool "${DD_RUM_TRACK_USER_INTERACTIONS:-true}"),
    trackLongTasks: $(js_bool "${DD_RUM_TRACK_LONG_TASKS:-true}"),
    defaultPrivacyLevel: "$(js_escape "${DD_RUM_DEFAULT_PRIVACY_LEVEL:-allow}")",
    allowedTracingUrls: $(js_array_from_csv "${DD_RUM_ALLOWED_TRACING_PATHS:-/api/}").map(function(path) {
      return window.location.origin + path;
    }),
    team: "$(js_escape "${DD_RUM_TEAM:-infra-cloud}")",
    application: "$(js_escape "${DD_RUM_APPLICATION:-observability-demo}")"
  }
};
EOF

exec "$@"
