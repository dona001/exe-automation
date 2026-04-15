FROM python:3.11-slim

# Install s3270 (headless 3270 terminal emulator)
RUN apt-get update && \
    apt-get install -y --no-install-recommends 3270-common s3270 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Create a directory for session files
RUN mkdir -p /app/sessions

EXPOSE 9995

ENV TE_PORT=9995

CMD ["python", "app.py"]
