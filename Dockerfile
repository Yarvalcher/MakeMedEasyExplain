# Use the official lightweight Python image
FROM python:3.11-slim

# Set environment variables to optimize Python container execution
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Install basic system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the dependency requirements file
COPY requirements.txt .

# Install dependencies (without caching to reduce image size)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the agent application code and local knowledge base wiki
COPY MMEE_Agent/ MMEE_Agent/
COPY knowledge_base/ knowledge_base/

# Expose the port (Cloud Run sets the PORT env variable automatically at runtime)
EXPOSE 8080

# Run the Flask dashboard server using Python
CMD ["python", "MMEE_Agent/app.py"]
