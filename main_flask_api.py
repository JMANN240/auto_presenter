from flask import Response, request, redirect, flash
from werkzeug.utils import secure_filename
import cv2, time, os, json, sqlite3
import numpy as np
from PIL import Image
from base64 import b64encode
from main_flask import app, gen_frames, gen_masks
import main_globals as settings
from io import BytesIO

# API routes

@app.route("/api/images", methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_images():
    if request.method == 'GET':
        img = request.args.get('image')
        if img is not None:
            return json.dumps(settings.imdb.load_row(img))
        return json.dumps(settings.imdb.load_all_rows())
    
    elif request.method == 'POST':
        file = request.files.get('file')
        unsafe_name = request.form.get('name')
        name = secure_filename(unsafe_name)
        try:
            settings.imdb.save_row(name, b64encode(file.read()), request.form.get('description'))
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
            settings.imdb.delete_row(img)
        else:
            flash(f"Please supply an image to delete")
            return "400"
        return "200"

@app.route("/api/saved_images", methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_saved_images():
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
def api_reset_servos():
    if settings.servo.enabled:
        settings.servo.reset()
    return "200"

@app.route('/api/overlay/image/<img>', methods=["POST"])
def api_overlay_image(img):
    settings.overlay.image(img, settings.imdb, settings.focus, 4*settings.radius)
    return "200"

@app.route('/api/overlay/arrow', methods=["POST"])
def api_overlay_arrow():
    settings.overlay.arrow(settings.focus)
    return "200"

@app.route('/api/overlay/save', methods=["POST"])
def api_save_overlay():
    if settings.onpi:
        stream = BytesIO()
        settings.camera.capture(stream, format='png')
        stream.seek(0)
        image = Image.open(stream)
    else:
        image = Image.fromarray(np.flip(settings.frame, 2))
    settings.overlay.draw(image).save(f"static/saved_images/{round(time.time())}.png")
    settings.overlay.clear()
    return "200"

@app.route('/api/set-target', methods=["POST"])
def api_set_target():
    if request.json['element'] == 'hue':
        settings.tgt_hsv[0] = int(request.json['value'])
    elif request.json['element'] == 'saturation':
        settings.tgt_hsv[1] = int(request.json['value'])
    elif request.json['element'] == 'value':
        settings.tgt_hsv[2] = int(request.json['value'])
    return "200"

@app.route('/api/set-variance', methods=["POST"])
def api_set_variance():
    if request.json['element'] == 'hue':
        settings.var_hsv[0] = int(request.json['value'])
    elif request.json['element'] == 'saturation':
        settings.var_hsv[1] = int(request.json['value'])
    elif request.json['element'] == 'value':
        settings.var_hsv[2] = int(request.json['value'])
    return "200"

@app.route('/api/calibrate', methods=["POST"])
def api_calibrate():
    if not settings.calibrated:
        frame_to_thresh = cv2.cvtColor(settings.frame, cv2.COLOR_BGR2HSV)
        settings.tgt_hsv = np.array(cv2.mean(frame_to_thresh, mask=settings.circle_img)[:3])
        settings.calibrated = True
    else:
        settings.calibrated = False
    return "200"

@app.route('/api/tgt-hsv', methods=["GET"])
def api_get_tgt_hsv():
    return f"{round(settings.tgt_hsv[0])} {round(settings.tgt_hsv[1])} {round(settings.tgt_hsv[2])}"

@app.route('/api/var-hsv', methods=["GET"])
def api_get_var_hsv():
    return f"{round(settings.var_hsv[0])} {round(settings.var_hsv[1])} {round(settings.var_hsv[2])}"

@app.route('/api/toggle-tracking', methods=['POST'])
def api_toggle_tracking():
    settings.tracking = not settings.tracking
    return "200"

@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    settings.running = False
    request.environ.get('werkzeug.server.shutdown')()
    return "200"