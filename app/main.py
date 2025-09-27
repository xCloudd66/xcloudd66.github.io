from flask import Flask, session, render_template, request, redirect, url_for, jsonify, flash, Response
import json
import time
from datetime import datetime, timedelta
import os
import logging
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import pandas as pd
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
import cv2

# Get the absolute path to the directory containing your script
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'instance', 'site.db')

app = Flask(__name__)
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")
app.secret_key = "557ac4e7bce40098e438983bc428c80a"
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy()
db.init_app(app)

class SabahDB(db.Model):
    __tablename__ = 'sabah'
    id = db.Column(db.Integer, primary_key=True)
    sabah = db.Column(db.String(255))

    @classmethod
    def get_or_create(cls):
        settings = cls.query.first()
        if settings is None:
            settings = cls()
            db.session.add(settings)
            db.session.commit()
        return settings

class NewsflashDB(db.Model):
    __tablename__ = 'newsflash'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)

# Initialize Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# Image folder for slideshow
image_folder = os.path.join(base_dir, 'static', 'images')
thumbnail_folder = os.path.join(image_folder, 'thumbnails')
allowed_extensions = {'jpg', 'jpeg', 'png', 'mp4'}
parent_dir = os.path.dirname(base_dir)
csv_file_path = os.path.join(parent_dir, 'raw_data', 'namaz_vakitleri_hamburg.csv')

# Configure basic logging
logging.basicConfig(filename='app.log', level=logging.INFO)

# Simple user management strategy
users = {'1': {'id': '1', 'username': 'admin', 'password_hash': generate_password_hash('test')}}

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user_data = users.get(user_id)
    if user_data:
        user = User()
        user.id = user_data['id']
        user.username = user_data['username']
        return user
    return None

# STARTSEITE = SLIDESHOW (öffentlich)
@app.route('/')
def home():
    image_files = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png', 'mp4'))]
    df = pd.read_csv(csv_file_path)
    today_date = pd.to_datetime('today').strftime('%d.%m.%Y')
    df = df[df['Tarih'] == today_date]
    tarih = df['Tarih'].values[0] if not df.empty else "N/A"
    
    if not df.empty:
        df = df.drop(columns=['Tarih'])
    else:
        df = pd.DataFrame()

    settings = SabahDB.get_or_create()
    return render_template('slideshow.html', title='IGN Slide', image_files=image_files, 
                          dataframe=df, date=tarih, sabah=settings.sabah)

# SLIDESHOW (weiterhin verfügbar unter /slideshow)
@app.route('/slideshow')
def public_slideshow():
    return redirect(url_for('home'))  # Weiterleitung zur Startseite

# ADMIN LOGIN
# main.py
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Check if the user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user_data = next((user for user in users.values() if user['username'] == username), None)
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = load_user(user_data['id'])
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')

    return render_template('login.html')

# ADMIN DASHBOARD
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_authenticated:
        flash("Please log in to access this page", "warning")
        return redirect(url_for('admin_login'))

    settings = SabahDB.get_or_create()
    image_files = [f for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png', '.mp4'))]
    
    return render_template('index.html', title='Admin Dashboard',
                          image_files=image_files, sabah=settings.sabah)

# ADMIN LOGOUT
@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('admin_login'))

# ADMIN BILD-UPLOAD
@app.route('/admin/upload', methods=['POST'])
@login_required
def admin_upload():
    try:
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '' and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                filename = secure_filename(file.filename)
                file.save(os.path.join(image_folder, filename))
                generate_thumbnail(filename)
                logging.info(f"File '{filename}' uploaded successfully.")
                socketio.emit('file_changed', {'message': 'File uploaded successfully'})
    except Exception as e:
        logging.error(f"Error during file upload: {str(e)}")
    return redirect(url_for('admin_dashboard'))

# ADMIN BILD-ENTFERNEN
@app.route('/admin/remove/<filename>')
@login_required
def admin_remove(filename):
    image_path = os.path.join(image_folder, filename)
    thumbnail_path = os.path.join(thumbnail_folder, 'thumb_' + filename)
    
    if os.path.exists(image_path):
        os.remove(image_path)
        logging.info(f"File '{filename}' removed.")
        socketio.emit('file_changed', {'message': 'File removed successfully'})

    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)
        logging.info(f"Thumbnail '{thumbnail_path}' removed.")

    return redirect(url_for('admin_dashboard'))

# Helper function
def generate_thumbnail(filename):
    image_path = os.path.join(image_folder, filename)
    thumbnail_path = os.path.join(thumbnail_folder, 'thumb_' + filename)

    if filename.endswith('.mp4'):
        thumbnail_filename = 'thumb_' + filename[:-4] + '.jpg'
        thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)
        cap = cv2.VideoCapture(image_path)

        if not cap.isOpened():
            return

        for _ in range(9):
            ret, frame = cap.read()
            if not ret:
                return

        ret, frame = cap.read()
        if ret:
            cv2.imwrite(thumbnail_path, frame)

        cap.release()
    else:
        with Image.open(image_path) as img:
            img.thumbnail((100, 100))
            img.save(thumbnail_path)

# SocketIO Events
@socketio.on('update_sabah')
def update_sabah(data):
    sabah_text = data.get('sabah', '')
    settings = SabahDB.get_or_create()
    settings.sabah = sabah_text
    db.session.commit()
    emit('sabah_updated', {'message': 'Sabah updated successfully'})

@socketio.on('get_newsflash')
def get_newsflash():
    entries = [entry.text for entry in NewsflashDB.query.all()]
    socketio.emit('newsflash_data', {'entries': entries})

@socketio.on('add_newsflash')
def add_newsflash(data):
    newsflash_text = data.get('newsflashText', '')
    new_entry = NewsflashDB(text=newsflash_text)
    db.session.add(new_entry)
    db.session.commit()
    entries = [entry.text for entry in NewsflashDB.query.all()]
    socketio.emit('newsflash_data', {'entries': entries})

@socketio.on('remove_newsflash')
def remove_newsflash(data):
    newsflash_text = data.get('newsflashText', '')
    entry_to_remove = NewsflashDB.query.filter_by(text=newsflash_text).first()
    if entry_to_remove:
        db.session.delete(entry_to_remove)
        db.session.commit()
        entries = [entry.text for entry in NewsflashDB.query.all()]
        socketio.emit('newsflash_data', {'entries': entries})

# API Routes
@app.route('/get_event_times')
def get_event_times():
    df2 = pd.read_csv(csv_file_path)
    today_date = pd.to_datetime('today').strftime('%d.%m.%Y')
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')

    df2_today = df2[df2['Tarih'] == today_date]
    df2_tomorrow = df2[df2['Tarih'] == tomorrow_date]
    df2_combined = pd.concat([df2_today, df2_tomorrow])

    if not df2_combined.empty:
        df2_combined = df2_combined.drop(columns=['Tarih'])
        event_times_values = df2_combined.values.tolist()
        return jsonify({'event_times_values': event_times_values})
    else:
        return jsonify({'error': 'No rows found in the DataFrame'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(host='0.0.0.0', port=8080, debug=True)