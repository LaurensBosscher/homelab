FROM oven/bun:1.3.5-debian

RUN rm /bin/sh && ln -s /bin/bash /bin/sh && mkdir -p /home/bun/ && chown bun:bun /home/bun/

USER bun
WORKDIR /home/bun/

RUN bun install opencode-ai oh-my-opencode@3.0.0-beta.2; bunx oh-my-opencode install --no-tui --claude=no --chatgpt=no --gemini=no

RUN echo 'export PATH="$HOME/.bun/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
ENV NODE_ENV=production

WORKDIR /workspace
CMD ["/home/bun/node_modules/opencode-ai/bin/opencode", "web", "--port", "4096", "--hostname", "0.0.0.0"]
