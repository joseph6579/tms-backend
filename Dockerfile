FROM python:3.11.0-alpine

ENV PYTHONUNBUFFERED=1

# Install runtime + build dependencies
RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    postgresql-dev \
    python3-dev \
    build-base \
    cargo \
    linux-headers \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    openblas-dev \
    libpng-dev \
    gdal \
    gdal-dev \
    geos-dev \
    py3-numpy

# Set working directory
WORKDIR /code

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x ./entrypoint.sh

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Optionally remove build dependencies (careful!)
# Only remove **after** requirements are successfully built
RUN apk del build-base gcc musl-dev python3-dev cargo linux-headers

# Run the app
ENTRYPOINT ["./entrypoint.sh"]
