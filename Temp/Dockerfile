# Use an official Python image as the base
FROM python:3.11-slim

# Set a working directory inside the container
WORKDIR /app

# Copy only the files needed for installation first (for caching)
COPY requirements.txt .

# Ensure requirements.txt has pinned versions before installing
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

#Set environment variables for security and clarity
ENV FLASK_APP=app_temp.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

EXPOSE 5000
CMD ["flask", "run"]

