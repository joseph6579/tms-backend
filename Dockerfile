FROM python:3.11-bullseye

ENV PYTHONUNBUFFERED=1 \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_VERSION=3.8.4

# Install required OS packages
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
    python3-gdal \
    libgeos-dev \
    binutils \
    && rm -rf /var/lib/apt/lists/*

# Confirm gdal-config exists
RUN which gdal-config && gdal-config --version

WORKDIR /code
COPY . .

RUN chmod +x ./entrypoint.sh

# Install Python deps
RUN pip install --upgrade pip

RUN pip install numpy \
 && pip install "GDAL==$(gdal-config --version)" \
 && pip install --no-cache-dir -r requirements.txt


ENTRYPOINT ["./entrypoint.sh"]
