FROM python:3.11-bullseye

ENV PYTHONUNBUFFERED=1 \
    CPLUS_INCLUDE_PATH=/usr/include/gdal \
    C_INCLUDE_PATH=/usr/include/gdal \
    GDAL_VERSION=3.8.4 \
    LD_LIBRARY_PATH=/usr/lib:/usr/lib/x86_64-linux-gnu

ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so.30

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

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Install Python deps
RUN pip install --upgrade pip
RUN pip install numpy
RUN pip install --no-cache-dir -r requirements.txt

#ENTRYPOINT ["./entrypoint.sh"]
