# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Expose port 5000 to the outside world
EXPOSE 5000

# Define environment variable to run python unbuffered
ENV PYTHONUNBUFFERED=1

# Run server.py when the container launches
CMD ["python", "server.py"]
