FROM python:3.11.0-alpine

ENV PYTHONUNBUFFERED 1

# Install build deps and lib dependencies
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
    libpng-dev

RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN chmod +x ./entrypoint.sh

RUN pip install -U pip
RUN pip install -r requirements.txt

RUN apk del build-base gcc musl-dev ...

# Ensure the entrypoint script has execute permissions

ENTRYPOINT ["./entrypoint.sh"]
