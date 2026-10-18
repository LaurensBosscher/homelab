#!/bin/sh
# Seed config on an empty volume. Later edits stay on the PVC so pairing
# tokens and runtime state are not wiped on every start.
set -eu

mkdir -p "${HOME}/.zeroclaw" "${ZEROCLAW_DATA_DIR}"

if [ ! -f "${HOME}/.zeroclaw/config.toml" ]; then
  cp /config/config.toml "${HOME}/.zeroclaw/config.toml"
  chmod 600 "${HOME}/.zeroclaw/config.toml"
fi

exec /usr/local/bin/zeroclaw daemon
