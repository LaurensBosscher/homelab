FROM oven/bun:1.3.14-debian

RUN rm /bin/sh && ln -s /bin/bash /bin/sh && mkdir -p /home/bun/ && chown bun:bun /home/bun/

USER bun
WORKDIR /home/bun/

RUN bun install opencode-ai@1.17.18 oh-my-opencode@4.16.3 && \
    bunx oh-my-opencode install --no-tui --claude=no --openai=no --gemini=no --copilot=no

RUN echo 'export PATH="$HOME/node_modules/opencode-ai/bin/:$PATH"' >> ~/.bashrc && source ~/.bashrc
ENV NODE_ENV=production

WORKDIR /home/bun/workspaces
CMD ["/home/bun/node_modules/opencode-ai/bin/opencode", "web", "--port", "4096", "--hostname", "0.0.0.0"]
