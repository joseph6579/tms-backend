FROM python:3.11.0-alpine

# Install necessary system dependencies
RUN apk add --no-cache gcc musl-dev libffi-dev

RUN mkdir /tms-backend
WORKDIR /tms-backend

# Copy requirements and install dependencies
COPY requirements.txt /tms-backend/requirements.txt
RUN pip install --no-cache-dir -r /tms-backend/requirements.txt

# Copy all necessary project files
COPY ../../ /tms-backend

ENV PYTHONUNBUFFERED=1

# Run Celery
CMD ["sh", "-c", "PYTHONPATH=/tms-backend:/tms-backend/tms celery -A tms flower --loglevel=info --basic_auth=${FLOWER_BASIC_AUTH}"]
