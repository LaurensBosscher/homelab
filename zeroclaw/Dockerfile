# Published all-features build (StageX, statically linked musl, no package
# manager). v0.8.6 tag matrix: all-features-v0.8.6 == floating all-features.
ARG ZEROCLAW_IMAGE=ghcr.io/zeroclaw-labs/zeroclaw:all-features-v0.8.6
FROM ${ZEROCLAW_IMAGE} AS zeroclaw

# Same CLI surface as OpenClaw (git, gh, kubectl, bun, opencode, browser, …).
# The all-features binary is static, so it runs on this glibc image.
FROM ghcr.io/laurensbosscher/openclaw-tools:2026.9.4

USER root

COPY --from=zeroclaw /usr/bin/zeroclaw /usr/local/bin/zeroclaw
COPY --from=zeroclaw /usr/bin/zerocode /usr/local/bin/zerocode
COPY --from=zeroclaw /usr/share/zeroclawlabs /usr/share/zeroclawlabs

# OpenClaw installs @googleworkspace/cli as `gog`. ZeroClaw looks up `gws`.
RUN ln -sf /usr/local/bin/gog /usr/local/bin/gws

COPY entrypoint.sh /usr/local/bin/zeroclaw-entrypoint
RUN chmod 755 /usr/local/bin/zeroclaw /usr/local/bin/zerocode /usr/local/bin/zeroclaw-entrypoint

ENV HOME=/zeroclaw-data \
    ZEROCLAW_DATA_DIR=/zeroclaw-data/data \
    ZEROCLAW_gateway__port=42617 \
    LANG=C.UTF-8 \
    CHROME_PATH=/usr/bin/brave-browser

USER node
WORKDIR /zeroclaw-data
EXPOSE 42617
ENTRYPOINT ["zeroclaw-entrypoint"]
