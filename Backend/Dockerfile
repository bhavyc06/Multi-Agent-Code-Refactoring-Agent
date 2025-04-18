FROM python:3.11-slim

WORKDIR /app

# 1️⃣ upgrade pip + install build tooling
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 2️⃣ copy lock/requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3️⃣ copy application code
COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
