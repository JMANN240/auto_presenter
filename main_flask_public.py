from flask import render_template
from main_flask import app

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
    return render_template('upload_overlay.html')