from flask import Flask, render_template, Response, request, redirect, flash
from werkzeug.utils import secure_filename
import cv2, time, os
import main_globals as settings
from main_cv import *


# Setup

app = Flask(__name__)
app.secret_key = os.urandom(24)

def gen_frames():
    while settings.running:
        f = settings.frame.copy()
        if settings.calibrated:
            cv2.circle(f, settings.focus, int(settings.radius), (0, 255, 255), 2)
            cv2.circle(f, settings.focus, 5, (0, 0, 255), -1)
        else:
            cv2.circle(f,(int(f.shape[1]/2),int(f.shape[0]/2)),settings.calibration_circle_size,(0,0,255),3)
        w = f.shape[1]
        h = f.shape[0]
        cv2.rectangle(f, (int(w/2-settings.target_square_size/2), int(h/2-settings.target_square_size/2)), (int(w/2+settings.target_square_size/2), int(h/2+settings.target_square_size/2)), (0,255,0), 1)
        _, prebuf = cv2.imencode('.jpg', f)
        buffer = prebuf.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')  # concat frame one by one and show result
        time.sleep(1/30)

def gen_masks():
    while settings.running:
        mask = generateMask(settings.frame)
        _, prebuf = cv2.imencode('.jpg', mask)
        buffer = prebuf.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')  # concat frame one by one and show result
        time.sleep(1/30)