FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/Zulko/moviepy.git@bc8d1a831d2d1f61abfdf1779e8df95d523947a5

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8001

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
