FROM python:3.11.0-alpine

ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN pip install -U pip
RUN pip install -r requirements.txt

# Ensure the entrypoint script has execute permissions
RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]