from flask import Flask, render_template, Response, request, redirect, flash
from werkzeug.utils import secure_filename
import cv2
import imutils
import sys
from imutils.video import VideoStream
import time
import threading
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
from image_db import ImageDatabase
import sqlite3
from base64 import b64decode, b64encode
from overlay_image import Overlay
import Adafruit_PCA9685


# Servo stuff

servo_enabled = True

try:
    pwm = Adafruit_PCA9685.PCA9685()
except:
    servo_enabled = False

accuracy_threshold = 10

t_angle = 150
t_min = 150
t_max = 650

p_angle = 150
p_min = 150
p_max = 1150

#Opencv stuff

camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
frame = np.zeros((int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), np.uint8)
running = True
tracking = True
focus = (0, 0)
scale = 0
radius = 0

avg_hsv = np.array((0,0,0))
var_hsv = np.array((0,0,0))

show_calibration_circle = True
calibration_radius = 100
calibrating = False
calibration_progress = 0
overlay = Overlay()

def generateMask(f):
    blurred = cv2.GaussianBlur(f, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, avg_hsv - var_hsv, avg_hsv + var_hsv)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    return mask

def getFrame():
    global camera, frame, running
    while running:
        success, frame = camera.read()

def showFrame():
    global frame, running, focus, radius, scale
    while running:
        f = np.copy(frame)
        mask = generateMask(f)
        cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            focus = (int(x), int(y))
            scale = radius*2
            cv2.circle(f, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            if tracking and servo_enabled:
                if (focus[0] < int(f.shape[1]/2) - accuracy_threshold):
                    pass
                elif (focus[0] > int(f.shape[1]/2) + accuracy_threshold):
                    pass
                if (focus[1] < int(f.shape[0]/2) - accuracy_threshold):
                    pass
                elif (focus[1] > int(f.shape[0]/2) + accuracy_threshold):
                    pass
        cv2.circle(f, focus, 5, (0, 0, 255), -1)
        cv2.circle(f,(int(f.shape[1]/2),int(f.shape[0]/2)),100,(0,0,255),3)
        



# Flask stuff

app = Flask(__name__)
app.secret_key = os.urandom(24)
imdb = ImageDatabase('database.db')


# Public routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/overlays')
def overlays():
    return render_template('overlays.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/upload')
def upload():
    return render_template('upload_image.html')


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
        return redirect("/gallery")
    
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
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/video_feed_mask')
def video_feed_mask():
    return Response(gen_masks(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/overlay/image/<img>', methods=["POST"])
def overlay_image(img):
    global overlay, imdb, focus, radius
    overlay.image(img, imdb, focus, 4*radius)
    return "200"

@app.route('/api/overlay/arrow', methods=["POST"])
def overlay_arrow():
    global overlay, focus
    overlay.arrow(focus)
    return "200"

@app.route('/api/overlay/save', methods=["POST"])
def save_overlay():
    global overlay, frame
    frame_image = Image.fromarray(np.flip(frame, 2))
    overlay.draw(frame_image).save(f"static/saved_images/{round(time.time())}.png")
    overlay.clear()
    return "200"

@app.route('/api/set-color', methods=["POST"])
def set_color():
    global var_hsv
    if request.json['element'] == 'hue':
        var_hsv[0] = int(request.json['value'])
    elif request.json['element'] == 'saturation':
        var_hsv[1] = int(request.json['value'])
    elif request.json['element'] == 'value':
        var_hsv[2] = int(request.json['value'])
    return "200"

@app.route('/api/calibrate', methods=["POST"])
def calibrate():
    global show_calibration_circle, var_hsv, avg_hsv, calibrating, calibration_progress
    show_calibration_circle = not show_calibration_circle
    if not show_calibration_circle:
        calibrating = True
        circle_img = np.zeros((frame.shape[0],frame.shape[1]), np.uint8)
        cv2.circle(circle_img,(int(frame.shape[1]/2),int(frame.shape[0]/2)),100,(255,255,255),-1)
        frame_to_thresh = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        avg_hsv = np.array(cv2.mean(frame_to_thresh, mask=circle_img)[:3])
        prev_best = 0
        prev_best_in = 0
        prev_best_out = 1
        for hv in range(0, 101, 10):
            for sv in range(0, 101, 10):
                for vv in range(0, 101, 10):
                    test_var_hsv = np.array((hv, sv, vv))
                    thresh = cv2.inRange(frame_to_thresh, avg_hsv-test_var_hsv, avg_hsv+test_var_hsv)
                    
                    in_mask = (thresh/255)*(circle_img/255)*255
                    out_mask = (thresh/255)*(((circle_img/255)-1)*(-1))*255

                    in_sum = np.sum(in_mask/255)
                    out_sum = np.sum(out_mask/255)

                    total_area = frame.shape[1] * frame.shape[0]
                    in_area = np.pi * (calibration_radius ** 2)
                    out_area = total_area - in_area

                    in_ratio = round(in_sum/in_area, 3)
                    out_ratio = round(out_sum/out_area, 3)

                    if out_ratio != 0 and in_ratio/out_ratio > prev_best and in_ratio > 0.8 and out_ratio < 0.1:
                        prev_best = in_ratio/out_ratio
                        var_hsv = test_var_hsv
                    calibration_progress+=1
    calibrating = False
    calibration_progress=0
    return str(var_hsv)

@app.route('/api/toggle-tracking', methods=['POST'])
def toggle_tracking():
    global tracking
    tracking = not tracking
    return "200"

@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    global running
    running = False
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    return "200"

def gen_frames():
    global frame, running, show_calibration_circle, calibrating, calibration_progress
    angle = 0
    while running:
        f = np.copy(frame)
        if show_calibration_circle:
            cv2.circle(f,(int(f.shape[1]/2),int(f.shape[0]/2)),calibration_radius,(0,0,255),3)
        if calibrating:
            cv2.ellipse(f, (int(f.shape[1]/2),int(f.shape[0]/2)), (calibration_radius, calibration_radius), angle%360, 0, calibration_progress/1331*360, (0,255,0), 3)
            angle+=10
        cv2.circle(f, focus, 5, (0, 0, 255), -1)
        ret, prebuf = cv2.imencode('.jpg', f)
        buffer = prebuf.tobytes()
        time.sleep(1/30)
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')  # concat frame one by one and show result

def gen_masks():
    global frame, running
    while running:
        mask = generateMask(frame)
        ret, prebuf = cv2.imencode('.jpg', mask)
        buffer = prebuf.tobytes()
        time.sleep(1/30)
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')  # concat frame one by one and show result

getFrameThread = threading.Thread(target=getFrame)
getFrameThread.name = "get frame"

showFrameThread = threading.Thread(target=showFrame)
showFrameThread.name = "show frame"

serverThread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 80})
serverThread.name = "server"

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'flask':
        app.run(debug=True)
    else:
        getFrameThread.start()
        showFrameThread.start()
        serverThread.start()
        getFrameThread.join()
        showFrameThread.join()
        serverThread.join()
        cv2.destroyAllWindows()