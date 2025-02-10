# Use the official Python image
FROM python:3.12.8-slim-bookworm

# Set environment variables to avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

ARG VERSION

# Set up a working directory
WORKDIR /app

# Copy application files
COPY dist/upstash_redis_local-${VERSION}-cp312-cp312-linux_x86_64.whl ./

# Install Python dependencies
RUN pip install --no-cache-dir upstash_redis_local-${VERSION}-cp312-cp312-linux_x86_64.whl

# Clean up
RUN rm /app/upstash_redis_local-${VERSION}-cp312-cp312-linux_x86_64.whl


# Default command
CMD ["python", "-m", "upstash_redis_local"]