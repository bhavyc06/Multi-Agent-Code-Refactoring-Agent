FROM python:3.11-slim
WORKDIR /srv
RUN pip install semgrep semgrep-mcp-server==0.0.6
ENV MCP_PORT=3903
CMD ["semgrep-mcp-server", "--dir", "/code", "--port", "3903"]
