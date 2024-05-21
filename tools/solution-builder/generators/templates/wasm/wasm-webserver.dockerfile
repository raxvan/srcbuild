# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .


# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=wasm-webhost.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose port 8080 for the Flask app
EXPOSE 8080

COPY wasm-webhost.py .

WORKDIR /runtime

COPY wasm-index.html .
