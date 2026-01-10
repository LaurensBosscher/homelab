FROM oven/bun:1.3.5-debian

RUN bun install -g opencode-ai oh-my-opencode@3.0.0-beta.2; bunx oh-my-opencode install --no-tui --claude=no --chatgpt=no --gemini=no

WORKDIR /workspace

ENV NODE_ENV=production
CMD ["opencode", "web", "--port", "4096", "--hostname", "0.0.0.0"]
