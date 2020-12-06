from flask import Flask
import csv
import os
import sys 
from google.cloud import vision
app = Flask(__name__)
app.secret_key = "asdfasfdasfdsafasddfsadfasdfsadfdas"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

base = os.getcwd()

@app.route('/')
def hello_world():
    client = vision.ImageAnnotatorClient()
    response = client.annotate_image({
        'image' : {'source' : {'image_uri' : "./test.jpg"}}
    })
    print(response, flush=True)
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
