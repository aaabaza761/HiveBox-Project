FROM python:3.11-slim 
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app_version.py . 
EXPOSE 5001
CMD [ "python","app_version.py" ]
