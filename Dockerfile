FROM python:3.11-bullseye

ENV PYTHONUNBUFFERED=1

# Install build tools and GDAL with apt
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

# Set GDAL environment variables for pip
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
ENV GDAL_VERSION=3.8.4

# Set working directory
WORKDIR /code

# Copy code
COPY . .

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

# Install dependencies
RUN pip install --upgrade pip
RUN pip install numpy  # Required before GDAL
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["./entrypoint.sh"]
