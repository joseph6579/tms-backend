FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libpq-dev \
    python3-dev \
    cargo \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libopenblas-dev \
    libpng-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Optional: preinstall numpy before GDAL to avoid array warning
RUN pip install --upgrade pip
RUN pip install numpy

# Set working directory
WORKDIR /code

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./entrypoint.sh"]
