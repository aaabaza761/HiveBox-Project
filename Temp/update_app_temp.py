from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta
import boto3

app = Flask(__name__)

@app.route('/average-temperature', methods=['GET'])
def average_temperature():
    # احسب الوقت الحالي و الوقت من ساعة
    now = datetime.utcnow()
    one_hour_ago = now - timedelta(hours=1)

    # حوّل التوقيت لصيغة ISO اللي الـ API بيقبلها
    from_date = one_hour_ago.isoformat() + 'Z'
    to_date = now.isoformat() + 'Z'

    # API Endpoint مع الباراميترز
    url = 'https://api.opensensemap.org/boxes/data'
    params = {
        'phenomenon': 'temperature',
        'from-date': from_date,
        'to-date': to_date
    }

    # ابعت request للـ API
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        return jsonify({'error': 'Failed to fetch data from openSenseMap API'}), 500

    data = response.json()
    print (data)