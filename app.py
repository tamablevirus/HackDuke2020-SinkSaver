from flask import Flask, request,url_for, send_file
import csv
import os
import sys 
from google.cloud import vision
from twilio.rest import Client
from datetime import datetime


app = Flask(__name__)
app.secret_key = "asdfasfdasfdsafasddfsadfasdfsadfdas"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
base = os.getcwd()

client = vision.ImageAnnotatorClient.from_service_account_file(
    os.path.normpath(os.path.normpath(base + '/sinksaver-82c12b4843e4.json')))
twilio_client = Client('AC12f0e70d75c3f685834f3c3de9ac888c','98325208aaeb18c12cb3b8ec8fbefc04')

last_time_water_running = -1

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
def upload(content):
    if request.files:
        image = request.files['dripFrame']
        image.save(os.path.join(base,'arduino.jpg'))
        image_helper_google('arduino.jpg')

def should_send_reminder(label_ann):
    global last_time_water_running
    for label in label_ann:
        desc = str(label.description).lower()
        if ('finger' in desc or 'hand' in desc or 'dog' in desc or 'paw' in desc or 'cat' in desc or 'toe' in desc) and label.score>=90.000:
            last_time_water_running = -1
            return False
        if ('liquid' in desc and label.score>=90.000) or ('fluid' in desc and label.score>=90.000):
            if type(last_time_water_running) is int:
                last_time_water_running = datetime.now()
                return False
            else:
                delt = datetime.now() - last_time_water_running
                if delt.days==0 and delt.seconds>=10:
                    last_time_water_running = -1
                    return True
                #Days should never be greater than 0, but in case it does happen somehow
                elif delt.days>0:
                    last_time_water_running = -1
                    return True


def image_helper_google(image):
    resp = client.annotate_image({
  'image': {'source': {'image_uri': 'https://sink-saver.herokuapp.com/image/'+image}},
  'features': [{'type_': vision.Feature.Type.LABEL_DETECTION}]
})

    #print(resp.label_annotations[0].description)

    if should_send_reminder(resp.label_annotations):
        twilio_client.messages.create(to='+19802290745',from_='+19104000202', body='Your sink has running water unattended. Please go turn it off!')

if __name__ == '__main__':
    #image_helper_google('test.jpg')
    app.run()
