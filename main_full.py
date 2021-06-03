from flask import Flask, render_template, Response, request, redirect, flash
from werkzeug.utils import secure_filename
import cv2
import imutils
import sys
import time
import threading
import os
import numpy as np
from PIL import Image
import json
from image_db import ImageDatabase
import sqlite3
from base64 import b64encode
from overlay_image import Overlay
import platform
from servo import Servo

# Configuration Variables

# Servo
accuracy_threshold = 40
move_amount = 10


# Servo stuff

servo_enabled = True

try:
    servo = Servo()
except:
    servo_enabled = False

#Opencv stuff

onpi = platform.system() == 'Linux'

if onpi:
    from picamera.array import PiRGBArray
    from picamera import PiCamera
    camera = PiCamera()
    resolution = (480, 368)
    framerate = 30
    camera.resolution = resolution
    camera.framerate = framerate
    rawCapture = PiRGBArray(camera, size=resolution)
    frame = np.zeros((resolution[1], resolution[0], 3), np.uint8)
else:
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    frame = np.zeros((int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), np.uint8)

running = True
tracking = True
focus = (0, 0)
scale = 0
radius = 0

tgt_hsv = np.array((0,0,0))
var_hsv = np.array((20,50,100))

calibration_radius = int(min(frame.shape[0], frame.shape[1]) * 0.25)
calibrated = False
overlay = Overlay()

def generateMask(f):
    blurred = cv2.GaussianBlur(f, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, tgt_hsv - var_hsv, tgt_hsv + var_hsv)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    return mask

def getFrame():
    global frame
    if onpi:
        for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            frame = f.array
            rawCapture.truncate(0)
            if not running:
                break
    else:
        while running:
            _, frame = camera.read()

def processFrame():
    global focus, radius, scale
    while running:
        mask = generateMask(frame)
        cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            focus = (int(x), int(y))
            scale = radius*2
            if tracking and servo_enabled and calibrated:
                if (focus[0] < int(frame.shape[1]/2) - accuracy_threshold):
                    servo.moveLeft(move_amount)
                elif (focus[0] > int(frame.shape[1]/2) + accuracy_threshold):
                    servo.moveRight(move_amount)
                if (focus[1] < int(frame.shape[0]/2) - accuracy_threshold):
                    servo.moveUp(move_amount)
                elif (focus[1] > int(frame.shape[0]/2) + accuracy_threshold):
                    servo.moveDown(move_amount)
        



# Flask stuff

app = Flask(__name__)
app.secret_key = os.urandom(24)
imdb = ImageDatabase('database.db')


# Public routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cpy')
def indexcpy():
    return render_template('index copy.html')

@app.route('/overlays')
def overlays():
    return render_template('overlays.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/upload')
def upload():
    return render_template('upload_overlay.html')


# API routes

@app.route("/api/images", methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_images():
    if request.method == 'GET':
        img = request.args.get('image')
        if img is not None:
            return json.dumps(imdb.load_row(img))
        return json.dumps(imdb.load_all_rows())
    
    elif request.method == 'POST':
        file = request.files.get('file')
        unsafe_name = request.form.get('name')
        name = secure_filename(unsafe_name)
        try:
            imdb.save_row(name, b64encode(file.read()), request.form.get('description'))
        except sqlite3.IntegrityError as e:
            if (str(e).split(':')[0] == "UNIQUE constraint failed"):
                flash(f"An image of the name '{request.form.get('name')}' already exists in the database")
            else:
                flash(str(e))
            return redirect("/upload")
        return redirect("/")
    
    elif request.method == 'DELETE':
        img = request.json.get('img')
        if img is not None:
            imdb.delete_row(img)
        else:
            flash(f"Please supply an image to delete")
            return "400"
        return "200"

@app.route("/api/saved_images", methods=['GET', 'POST', 'PUT', 'DELETE'])
def saved_images():
    if request.method == 'GET':
        return json.dumps([f for f in os.listdir('static/saved_images')])
    
    elif request.method == 'POST':
        pass
    
    elif request.method == 'DELETE':
        img = request.json.get('img')
        if img is None:
            flash(f"Please supply an image to delete")
            return "400"
        if not os.path.exists(os.path.join('static/saved_images/', img)):
            flash(f"The specified image does not exist")
            return "400"
        os.remove(os.path.join('static/saved_images/', img))
        return "200"

@app.route('/api/video_feed')
def api_video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/video_feed_mask')
def api_video_feed_mask():
    return Response(gen_masks(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/reset-servos', methods=["POST"])
def reset_servos():
    if servo_enabled:
        servo.reset()
    return "200"

@app.route('/api/overlay/image/<img>', methods=["POST"])
def overlay_image(img):
    overlay.image(img, imdb, focus, 4*radius)
    return "200"

@app.route('/api/overlay/arrow', methods=["POST"])
def overlay_arrow():
    overlay.arrow(focus)
    return "200"

@app.route('/api/overlay/save', methods=["POST"])
def save_overlay():
    frame_image = Image.fromarray(np.flip(frame, 2))
    overlay.draw(frame_image).save(f"static/saved_images/{round(time.time())}.png")
    overlay.clear()
    return "200"

@app.route('/api/set-target', methods=["POST"])
def set_target():
    global tgt_hsv
    if request.json['element'] == 'hue':
        tgt_hsv[0] = int(request.json['value'])
    elif request.json['element'] == 'saturation':
        tgt_hsv[1] = int(request.json['value'])
    elif request.json['element'] == 'value':
        tgt_hsv[2] = int(request.json['value'])
    return "200"

@app.route('/api/set-variance', methods=["POST"])
def set_variance():
    global var_hsv
    if request.json['element'] == 'hue':
        var_hsv[0] = int(request.json['value'])
    elif request.json['element'] == 'saturation':
        var_hsv[1] = int(request.json['value'])
    elif request.json['element'] == 'value':
        var_hsv[2] = int(request.json['value'])
    return "200"

circle_img = np.zeros((frame.shape[0],frame.shape[1]), np.uint8)
cv2.circle(circle_img,(int(frame.shape[1]/2),int(frame.shape[0]/2)),100,(255,255,255),-1)

@app.route('/api/calibrate', methods=["POST"])
def calibrate():
    global tgt_hsv, calibrated
    if not calibrated:
        frame_to_thresh = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        tgt_hsv = np.array(cv2.mean(frame_to_thresh, mask=circle_img)[:3])
        calibrated = True
    else:
        calibrated = False
    return "200"

@app.route('/api/tgt-hsv', methods=["GET"])
def get_tgt_hsv():
    return f"{round(tgt_hsv[0])} {round(tgt_hsv[1])} {round(tgt_hsv[2])}"

@app.route('/api/var-hsv', methods=["GET"])
def get_var_hsv():
    return f"{round(var_hsv[0])} {round(var_hsv[1])} {round(var_hsv[2])}"

@app.route('/api/toggle-tracking', methods=['POST'])
def toggle_tracking():
    global tracking
    tracking = not tracking
    return "200"

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    global running
    running = False
    request.environ.get('werkzeug.server.shutdown')()
    return "200"

def gen_frames():
    while running:
        f = frame.copy()
        cv2.circle(f, focus, int(radius), (0, 255, 255), 2)
        cv2.circle(f, focus, 5, (0, 0, 255), -1)
        if not calibrated:
            cv2.circle(f,(int(f.shape[1]/2),int(f.shape[0]/2)),calibration_radius,(0,0,255),3)
        cv2.rectangle(f, (int(f.shape[1]/2-accuracy_threshold),int(f.shape[0]/2-accuracy_threshold)), (int(f.shape[1]/2+accuracy_threshold),int(f.shape[0]/2+accuracy_threshold)), (0,255,0), 1)
        ret, prebuf = cv2.imencode('.jpg', f)
        buffer = prebuf.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')  # concat frame one by one and show result
        time.sleep(1/30)

def gen_masks():
    global frame, running
    while running:
        mask = generateMask(frame)
        _, prebuf = cv2.imencode('.jpg', mask)
        buffer = prebuf.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')  # concat frame one by one and show result
        time.sleep(1/30)

getFrameThread = threading.Thread(target=getFrame)
getFrameThread.name = "get frame"

processFrameThread = threading.Thread(target=processFrame)
processFrameThread.name = "process frame"

serverThread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8000})
serverThread.name = "server"

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'flask':
        app.run(debug=True)
    else:
        getFrameThread.start()
        processFrameThread.start()
        serverThread.start()
        getFrameThread.join()
        processFrameThread.join()
        serverThread.join()
        cv2.destroyAllWindows()