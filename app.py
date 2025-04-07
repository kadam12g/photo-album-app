#!/usr/bin/env python3

# app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World! This photo album app is running on Kubernetes!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

