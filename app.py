from flask import Flask, request, send_file, session
import os
import json
from google.cloud import vision
from twilio.rest import Client
from datetime import datetime

#Setting up basic server stuff
app = Flask(__name__)
app.secret_key = "asdfasfdasfdsafasddfsadfasdfsadfdas"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
base = os.getcwd()
app.config['UPLOAD_FOLDER'] = base +'/static'

import random
import string

#Storing our google authentication service account in a secure, unknown place within the server
json_file_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
with open(os.path.join(app.config['UPLOAD_FOLDER'],json_file_name+'.json'), 'w') as json_fi:
    json.dump(json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS']), json_fi)

#Initialize Google Vision
client = vision.ImageAnnotatorClient.from_service_account_file(os.path.join(app.config['UPLOAD_FOLDER'],json_file_name+'.json'))
#Initialize Twilio
twilio_client = Client(os.environ['TWILIO_SID'],os.environ['TWILIO_AUTH'])


@app.route('/')
def hello_world():
    return 'The website is not intended to be used like this'


#Retrieves images sent by Arduino
@app.route("/image/<name>", methods=["GET"])
def getImage(name):
    return send_file(app.config['UPLOAD_FOLDER']+'/'+name, mimetype="image")

#Saves images received by server from the Arduino to a temporary spot on the server
@app.route("/upload", methods=["POST"])
def upload():
    print(request.files)
    if request.files:
        if not('last_time_water_running' in session.keys()):
            session['last_time_water_running'] = -1
        image = request.files['dripFrame']
        image.save(os.path.join(app.config['UPLOAD_FOLDER'],'arduino.jpg'))
        print('LAST DATE: ' + str(session['last_time_water_running']))
        image_helper_google('arduino.jpg')
        return 'Success'
    return 'Failed'

#Checks to see if there are obstructions,
# and if there are not and it has been longer than 10 seconds since a faucet has been running, then return True
def should_send_reminder(label_ann):
    #global last_time_water_running
    for label in label_ann:
        desc = str(label.description).lower()
        print("LOOKING... " +desc + ","+str(label.score))

        #Detect obstruction in faucet
        if ('finger' in desc or 'hand' in desc or 'dog' in desc or 'paw' in desc or 'cat' in desc or 'toe' in desc) and label.score>=0.90000:
            print("OBSTRUCTION FOUND")
            session['last_time_water_running'] = -1
            return False

        #If there are no obstructions, then detect for liquid and fluid within faucet frame
        if ('liquid' in desc and label.score>=0.90000) or ('fluid' in desc and label.score>=0.90000):
            print("OBSTRUCTION NOT FOUND")
            if type(session['last_time_water_running']) is int:
                session['last_time_water_running'] = datetime.now()
                print("===SET NEW TIME===")
                return False
            else:
                print("CHECKING TIME DIFFERENCE")
                delt = datetime.now() - session['last_time_water_running']
                #If it has been at least 10 seconds that the water has been running, then return True so that a text will be sent via Twilio
                if delt.days==0 and delt.seconds>=10:
                    session['last_time_water_running'] = -1
                    return True
                #Days should never be greater than 0, but in case it does happen somehow
                elif delt.days>0:
                    session['last_time_water_running'] = -1
                    return True
    return False

def image_helper_google(image):
    #Send Arduino image to Google's Vision API and receive a response
    resp = client.annotate_image({
  'image': {'source': {'image_uri': 'https://sink-saver.herokuapp.com/image/'+image}},
  'features': [{'type_': vision.Feature.Type.LABEL_DETECTION}]
})

    #Check to see if text should be sent
    if should_send_reminder(resp.label_annotations):
        print('SENDING TEXT....')
        #Send text
        twilio_client.messages.create(to=os.environ['TO_NUMBER'],from_='+19104000202',
                                      body='[SinkSaver] Your sink has running water unattended. Please go turn it off!')

if __name__ == '__main__':
    session.clear()
    app.run()
