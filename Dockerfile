FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (leverages Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create data directory for SQLite database
RUN mkdir -p /app/data

# SQLite database is stored in a volume-mounted directory
VOLUME /app/data

CMD ["python", "main.py"]
