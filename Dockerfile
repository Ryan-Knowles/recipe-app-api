FROM python:3.7-alpine
LABEL maintainer="Ryan Knowles <ryan.knowles@brigevine.com>"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN pip install -r requirements.txt

RUN mkdir /app
COPY ./app /app
WORKDIR /app

RUN adduser -D py-user
USER py-user

