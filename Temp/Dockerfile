FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY appVersion.py .
FROM python:3.11-slim 
WORKDIR /app
COPY --from=builder /app . 
CMD [ "python","appVersion" ]