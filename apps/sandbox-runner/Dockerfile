FROM python:3.11-slim

# Install Node.js for JavaScript/TypeScript execution
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install TypeScript and tsx globally
RUN npm install -g typescript tsx

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create execution directory
RUN mkdir -p /tmp/sandbox && chmod 777 /tmp/sandbox

# Create non-root user for running code
RUN useradd -m -u 1000 sandbox && chown -R sandbox:sandbox /app /tmp/sandbox

# Expose port
EXPOSE 8080

# Run as root initially (server will drop privileges for code execution)
CMD ["python", "server.py"]
