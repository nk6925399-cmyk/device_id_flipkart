# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install MongoDB Python packages
RUN pip install --no-cache-dir pymongo dnspython

# CRITICAL: Create devices.json if it doesn't exist, and grant full read/write permissions (0666)
RUN touch /app/devices.json && chmod 0666 /app/devices.json

# Expose port 5000 to the outside world
EXPOSE 5000

# Define environment variable to run python unbuffered
ENV PYTHONUNBUFFERED=1

# Run server.py when the container launches
CMD ["python", "server.py"]
