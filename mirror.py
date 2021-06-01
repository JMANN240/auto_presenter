from flask import Flask, render_template, Response, request
import cv2
from imutils.video import VideoStream
import time
import threading
import platform
import os
import numpy as np

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

def getFrame():
    global camera, frame, running, onpi
    if onpi:
        #global rawCapture
        for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
            frame = f.array
            rawCapture.truncate(0)
            if not running:
                break
    else:
        while running:
            _, frame = camera.read()

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/')
def index():
    return render_template('mirror.html')

@app.route('/api/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/shutdown', methods=['POST'])
def shutdown():
    global running
    running = False
    func = request.environ.get('werkzeug.server.shutdown')
    func()
    return "200"

def gen_frames():
    global frame, running
    while running:
        ret, prebuf = cv2.imencode('.jpg', frame)
        buffer = prebuf.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')  # concat frame one by one and show result
        time.sleep(1/framerate)

getFrameThread = threading.Thread(target=getFrame)
getFrameThread.name = "get frame"

serverThread = threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 8000})
serverThread.name = "server"

if __name__ == "__main__":
    getFrameThread.start()
    serverThread.start()
    getFrameThread.join()
    serverThread.join()
