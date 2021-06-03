import cv2, imutils
import main_globals as settings

def generateMask(f):
    blurred = cv2.GaussianBlur(f, (11, 11), 0)
    hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, settings.tgt_hsv - settings.var_hsv, settings.tgt_hsv + settings.var_hsv)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    return mask

def getFrame():
    if settings.onpi:
        for f in settings.camera.capture_continuous(settings.rawCapture, format="bgr", use_video_port=True):
            settings.frame = f.array
            settings.rawCapture.truncate(0)
            if not settings.running:
                break
    else:
        while settings.running:
            _, settings.frame = settings.camera.read()

def processFrame():
    while settings.running:
        mask = generateMask(settings.frame)
        cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        if len(cnts) > 0:
            c = max(cnts, key=cv2.contourArea)
            ((x, y), settings.radius) = cv2.minEnclosingCircle(c)
            settings.focus = (int(x), int(y))
            settings.scale = settings.radius*2
            if settings.tracking and settings.servo.enabled and settings.calibrated:
                if (settings.focus[0] < int(settings.frame.shape[1]/2) - int(settings.frame.shape[1]/2*settings.target_square_size/2)):
                    settings.servo.moveLeft(settings.move_amount)
                elif (settings.focus[0] > int(settings.frame.shape[1]/2) + int(settings.frame.shape[1]/2*settings.target_square_size/2)):
                    settings.servo.moveRight(settings.move_amount)
                if (settings.focus[1] < int(settings.frame.shape[0]/2) - int(settings.frame.shape[0]/2*settings.target_square_size/2)):
                    settings.servo.moveUp(settings.move_amount)
                elif (settings.focus[1] > int(settings.frame.shape[0]/2) + int(settings.frame.shape[0]/2*settings.target_square_size/2)):
                    settings.servo.moveDown(settings.move_amount)