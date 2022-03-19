FROM python:3.10-alpine

LABEL Farrar142 "gksdjf1690@gmail.com"

ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

COPY . .
RUN apk update && apk add python3-dev \
                        gcc \
                        libc-dev \
                         libffi-dev
RUN pip3 install -r requirements.txt

# ENTRYPOINT python3 manage.py makemigrations && python3 manage.py migrate && tail -f /dev/null
EXPOSE 8888
ENTRYPOINT python3 manage.py makemigrations && python3 manage.py migrate && uvicorn base.asgi:application --reload --host 0.0.0.0 --port 8888