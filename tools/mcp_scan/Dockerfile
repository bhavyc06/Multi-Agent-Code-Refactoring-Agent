FROM python:3.11-slim
WORKDIR /usr/src
RUN pip install fastapi uvicorn pydantic bandit
COPY server.py .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
