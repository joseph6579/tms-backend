FROM python:3.11.0-alpine

RUN mkdir /code
WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./code

ENV PYTHONUNBUFFERED=1

CMD ["celery", "-A", "tms", "flower", "--loglevel=info"]