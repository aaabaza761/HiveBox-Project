FROM python:latest
WORKDIR /app
COPY /appVersion .
CMD [ "python","appVersion" ]ح