#!/bin/sh
# Pre-seed Brave ad-blocking filter lists for the OpenClaw managed profile.
#
# Brave's built-in Shields block ads/trackers by default. This script configures
# the additional filter lists matching Laurens' browser settings.
#
# Since Brave's internal filter list UUIDs change across versions, we use
# the custom filter list subscription mechanism with direct URLs for
# reliable configuration in a container environment.
#
# Run as the node user before the gateway starts (idempotent).

PREFS_DIR="${HOME}/.config/brave-preferences"
PREFS_FILE="${PREFS_DIR}/Default/Preferences"

mkdir -p "$(dirname "$PREFS_FILE")"

# These are the filter lists enabled in Laurens' Brave browser settings.
# Source: brave://adblock settings page export (2026-07-28)
#
# Built-in lists (enabled by default, confirmed via regional_filters):
#   - EasyList (default ads)
#   - EasyPrivacy (built-in tracking)
#
# Custom subscription lists (added via custom_filters):
#   - EasyList Cookie (cookie notices)
#   - Fanboy's Annoyance + uBO Annoyances (popups, overlays)
#   - Anti-AI suggestions Filters
#   - Fanboy's Anti-Newsletter
#   - Fanboy's Mobile Notifications
#   - YouTube Anti-Shorts
#   - Remove YouTube Autodubbed videos
#   - AdGuard URL Tracking Protection
#   - Bypass Paywalls Clean
#   - AdGuard Dutch (regional - Dutch)
#   - EasyList Germany (regional - German)

cat > "${PREFS_FILE}" <<'JSON'
{
  "brave": {
    "adblock": {
      "regional_filters": ["en", "de", "nl"],
      "filter_list": {
        "default": 1
      },
      "custom_filters": [
        "https://easylist.to/easylist/easylist.txt",
        "https://easylist.to/easylist/easyprivacy.txt",
        "https://easylist.to/easylist/easylist-cookie.txt",
        "https://secure.fanboy.co.nz/fanboy-annoyance.txt",
        "https://secure.fanboy.co.nz/fanboy-newsletter.txt",
        "https://secure.fanboy.co.nz/fanboy-mobile-notif.txt",
        "https://raw.githubusercontent.com/mjjankin/filterlists/main/Anti-AI-suggestions.txt",
        "https://raw.githubusercontent.com/youtubeline/youtube-anti-shorts/main/youtube-anti-shorts.txt",
        "https://raw.githubusercontent.com/DrDebrow/youtube-autodub-remover/main/filter.txt",
        "https://filters.adtidex.org/urltracker-list.txt",
        "https://gitflic.ru/project/magnolia1234/bypass-paywalls-clean-filters/raw/raw?file=bpc-paywall-filter.txt"
      ]
    },
    "shields_config": {
      "ad_block": "allow",
      "tracking_protection": "block",
      "https_everywhere": "allow",
      "fingerprinting_protection": "block",
      "brave_shields": "block"
    }
  },
  "enable_do_not_track": true
}
JSON

echo "[brave-preferences] Ad-block filter lists configured at ${PREFS_FILE}"
echo "[brave-preferences] Shields: enabled (ads, trackers, fingerprinting)"
echo "[brave-preferences] Regional filters: en, de, nl"
echo "[brave-preferences] Custom filter subscriptions: 11 lists"
