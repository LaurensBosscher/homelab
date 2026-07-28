#!/bin/sh
# Pre-seed Brave ad-blocking filter lists for the OpenClaw managed profile.
# Brave's built-in Shields block ads/trackers by default; this enables
# additional filter lists for stronger protection.
#
# Run as the node user before the gateway starts (idempotent).

PREFS_DIR="${HOME}/.config/brave-preferences"
PREFS_FILE="${PREFS_DIR}/Default/Preferences"

mkdir -p "$(dirname "$PREFS_FILE")"

# Default filter list state. Brave stores these as UUIDs.
# These are the standard EasyList + privacy + annoyance lists.
# Values: 1 = enabled, 0 = disabled
DEFAULT_REGION="en"

cat > "${PREFS_FILE}" <<'JSON'
{
  "brave": {
    "adblock": {
      "custom_filters": [],
      "regional_filters": ["en"],
      "filter_list": {
        "default": 1
      },
      "other_filters": {
        "https://easylist.to/easylist/easylist.txt": 1,
        "https://easylist.to/easylist/easyprivacy.txt": 1,
        "https://easylist.to/easylist/fanboy-annoyance.txt": 1,
        "https://easylist.to/easylist/fanboy-social.txt": 1,
        "https://malware-filter.gitlab.io/malware-filter/urlhaus-filter.txt": 1
      }
    },
    "shields_config": {
      "ad_block": "allow",
      "tracking_protection": "block",
      "https_everywhere": "allow",
      "fingerprinting_protection": "block",
      "brave_shields": "block"
    }
  }
}
JSON

echo "[brave-preferences] Ad-block filter lists configured at ${PREFS_FILE}"
