import cv2, platform
import numpy as np
from time import sleep
from image_db import ImageDatabase
from overlay_image import Overlay
from servo import Servo

def init():
    global target_square_size, move_amount
    global running, tracking, focus, scale, radius
    global tgt_hsv, var_hsv
    global calibration_circle_size, calibrated, circle_img
    global imdb, overlay, servo

    initializeCamera()

    target_square_size = 0.2 # Target square side length as a percentage of the smaller of the two frame dimensions
    calibration_circle_size = 0.2 # Target circle radius as a percentage of the smaller of the two frame dimensions
    target_square_size = int(min(frame.shape[0], frame.shape[1]) * target_square_size) # Calculating actual square size
    calibration_circle_size = int(min(frame.shape[0], frame.shape[1]) * calibration_circle_size) # Calculating actual circle radius
    move_amount = 4 # How much the servo moves to reach the target square

    running = True
    tracking = True
    focus = (0, 0)
    scale = 0
    radius = 0

    tgt_hsv = np.array((0,0,0))
    var_hsv = np.array((20,50,100))
    calibrated = False

    # Initializing custom objects
    imdb = ImageDatabase('database.db')
    servo = Servo()
    overlay = Overlay()

    circle_img = np.zeros((frame.shape[0],frame.shape[1]), np.uint8)
    cv2.circle(circle_img,(int(frame.shape[1]/2),int(frame.shape[0]/2)),calibration_circle_size,(255,255,255),-1)

def initializeCamera():
    global onpi, camera, rawCapture, frame
    onpi = platform.system() == 'Linux'
    if onpi:
        from picamera.array import PiRGBArray
        from picamera import PiCamera
        camera = PiCamera()
        sleep(2)
        resolution = (480, 368)
        framerate = 30
        camera.resolution = resolution
        camera.framerate = framerate
        rawCapture = PiRGBArray(camera, size=resolution)
        frame = np.zeros((resolution[1], resolution[0], 3), np.uint8)
    else:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        sleep(2)
        frame = np.zeros((int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)), 3), np.uint8)