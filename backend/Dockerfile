# 1. Use an official Python runtime as a parent image
# Using a specific version is recommended for reproducibility.
# '-slim' variants are smaller but might lack some OS libraries if needed.
FROM python:3.12-slim

# 2. Set environment variables
# Prevents Python from writing pyc files to disc (optional)
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr (recommended for logs)
ENV PYTHONUNBUFFERED 1

# 3. Set the working directory in the container
WORKDIR /app

# 4. Install system dependencies (if any)
# Example: If you needed build tools or specific libraries for a package
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
# First, copy only the requirements file to leverage Docker cache
COPY requirements.txt .
# Install dependencies specified in requirements.txt
# --no-cache-dir reduces image size
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of your application code into the container
COPY . .

# 7. Expose the port the app runs on
# This is documentation; the actual mapping is done in docker-compose.yml
EXPOSE 8000

# 8. Define the command to run your application
# This will be overridden by the 'command:' in docker-compose.yaml,
# but it's good practice to define a default command for the image.
CMD ["python", "app.py"]
