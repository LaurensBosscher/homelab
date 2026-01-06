# Use Node.js as base image
FROM node:20-slim

# Install dependencies for Bun
# Bun requires: curl (to download), unzip (to extract)
RUN apt-get update && apt-get install -y curl unzip

# Install OpenCode globally
RUN npm install -g opencode-ai

# Install oh-my-opencode globally
RUN npm install -g oh-my-opencode

# Create a working directory for the container
WORKDIR /workspace

# Expose port 4096 (default OpenCode web port)
EXPOSE 4096

# Set environment variables
ENV NODE_ENV=production

# Start OpenCode web server
# Listening on all interfaces (0.0.0.0) and port 4096
CMD ["opencode", "web", "--port", "4096", "--hostname", "0.0.0.0"]
