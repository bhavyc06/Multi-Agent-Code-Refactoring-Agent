FROM python:3.11-slim
WORKDIR /srv
RUN pip install shell-mcp-server==0.1.5
ENV MCP_PORT=3902
CMD ["shell-mcp-server", "/code", "--port", "3902", "--timeout", "15"]
