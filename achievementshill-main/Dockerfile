# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

RUN pip3 install pyrebase4 flask gunicorn python-dotenv


COPY . .

CMD [ "gunicorn", "--bind" , "0.0.0.0:5000", "wsgi:app" ]