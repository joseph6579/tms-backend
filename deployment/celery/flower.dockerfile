FROM python:3.11.0-alpine

RUN mkdir /tms-backend
WORKDIR /tms-backend

# Copy requirements and install dependencies
COPY requirements.txt /tms-backend/requirements.txt
RUN pip install --no-cache-dir -r /tms-backend/requirements.txt

# Copy all necessary project files
COPY . /tms-backend/

ENV PYTHONUNBUFFERED=1

CMD ["celery", "-A", "tms", "flower", "--loglevel=info"]
