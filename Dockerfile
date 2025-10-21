# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install RustDesk (example, adjust as needed)
# RUN curl -sL https://github.com/rustdesk/rustdesk/releases/download/1.1.9/rustdesk-1.1.9.deb -o rustdesk.deb \
#     && apt-get install -y --no-install-recommends ./rustdesk.deb \
#     && rm rustdesk.deb

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create a non-root user and switch to it
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "rustdesk_mcp.server:app", "--host", "0.0.0.0", "--port", "8000"]
