# Use an official Python image as the base
FROM python:3.11-slim

# Set a working directory inside the container
WORKDIR /app

# Copy only the files needed for installation first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set environment variables for security and clarity
ENV FLASK_APP=app_temp.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Expose the port the app will run on
EXPOSE 5000

# Define the command to run the app
CMD ["flask", "run"]
