FROM node:20-alpine
WORKDIR /srv
RUN npm install -g @modelcontextprotocol/server-filesystem
ENV MCP_PORT=3901
CMD ["mcp-server-filesystem", "/code", "--port", "3901"]
