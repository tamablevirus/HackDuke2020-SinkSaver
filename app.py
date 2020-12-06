from flask import Flask, request,url_for, send_file, session
import csv
import os
import json
import sys 
from google.cloud import vision
from twilio.rest import Client
from datetime import datetime

app = Flask(__name__)
app.secret_key = "asdfasfdasfdsafasddfsadfasdfsadfdas"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
base = os.getcwd()
app.config['UPLOAD_FOLDER'] = base +'/static'


client = vision.ImageAnnotatorClient.from_service_account_file(base+'/key.json')
twilio_client = Client(os.environ['TWILIO_SID'],os.environ['TWILIO_AUTH'])

#last_time_water_running = -1

@app.route('/')
def hello_world():
    return 'The website is not intended to be used like this'


@app.route("/image/<name>", methods=["GET"])
def getImage(name):
    return send_file(app.config['UPLOAD_FOLDER']+'/'+name, mimetype="image")
@app.route("/upload", methods=["POST"])
def upload():
    print(request.files)
    #global last_time_water_running
    if request.files:
        if not('last_time_water_running' in session.keys()):
            session['last_time_water_running'] = -1
        image = request.files['dripFrame']
        image.save(os.path.join(app.config['UPLOAD_FOLDER'],'arduino.jpg'))
        print('LAST DATE: ' + str(session['last_time_water_running']))
        image_helper_google('arduino.jpg')
        return 'Success'
    return 'Failed'

def should_send_reminder(label_ann):
    #global last_time_water_running
    for label in label_ann:
        desc = str(label.description).lower()
        if ('finger' in desc or 'hand' in desc or 'dog' in desc or 'paw' in desc or 'cat' in desc or 'toe' in desc) and label.score>=90.000:
            session['last_time_water_running'] = -1
            return False
        if ('liquid' in desc and label.score>=90.000) or ('fluid' in desc and label.score>=90.000):
            if type(session['last_time_water_running']) is int:
                session['last_time_water_running'] = datetime.now()
                return False
            else:
                delt = datetime.now() - session['last_time_water_running']
                if delt.days==0 and delt.seconds>=10:
                    session['last_time_water_running'] = -1
                    return True
                #Days should never be greater than 0, but in case it does happen somehow
                elif delt.days>0:
                    session['last_time_water_running'] = -1
                    return True
    return False

def image_helper_google(image):
    resp = client.annotate_image({
  'image': {'source': {'image_uri': 'https://sink-saver.herokuapp.com/image/'+image}},
  'features': [{'type_': vision.Feature.Type.LABEL_DETECTION}]
})

    #print(resp.label_annotations[0].description)

    if should_send_reminder(resp.label_annotations):
        print('SENDING TEXT....')
        twilio_client.messages.create(to='+19802290745',from_='+19104000202', body='[SinkSaver] Your sink has running water unattended. Please go turn it off!')

if __name__ == '__main__':
    #image_helper_google('test.jpg')
    app.run()
