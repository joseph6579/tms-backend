FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

# Install runtime + build dependencies using apt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libpq-dev \
    python3-dev \
    cargo \
    linux-headers-amd64 \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    libopenblas-dev \
    libpng-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for GDAL to build correctly
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Set working directory
WORKDIR /code

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir numpy  # prevent GDAL numpy warnings
RUN pip install --no-cache-dir -r requirements.txt

# Run the app
ENTRYPOINT ["./entrypoint.sh"]
