from flask import Flask, request,url_for, send_file
import csv
import os
import sys 
from google.cloud import vision

app = Flask(__name__)
app.secret_key = "asdfasfdasfdsafasddfsadfasdfsadfdas"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
base = os.getcwd()

client = vision.ImageAnnotatorClient.from_service_account_file(
    os.path.normpath(os.path.normpath(base + '/sinksaver-82c12b4843e4.json')))

@app.route('/')
def hello_world():
    client = vision.ImageAnnotatorClient.from_service_account_file(
        os.path.normpath(os.path.normpath(base + '/sinksaver-82c12b4843e4.json')))
    response = client.annotate_image({
        'image' : {'source' : {'image_uri' : "https://sink-saver.herokuapp.com/image"}}
    })
    print(response, flush=True)
    return 'Hello World!'


@app.route("/image/<name>", methods=["GET"])
def getImage(name):
    return send_file(name, mimetype="image")
@app.route("/upload/<content>", methods=["POST"])
def upload():
    image_helper_google(request.files['image'])

def image_helper_google(image):
    req = {
        "image": {"source": {'filename': ''}},
        "features": [
            {"type": vision.Feature.Type.LABEL_DETECTION},
        ]
    }
    resp = client.annotate_image({
  'image': {'source': {'image_uri': 'https://sink-saver.herokuapp.com/image/'+image}},
  'features': [{'type_': vision.Feature.Type.FACE_DETECTION}]
})


    print(resp)

if __name__ == '__main__':
    image_helper_google('test.jpg')
    app.run()
