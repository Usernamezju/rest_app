from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__,
                static_folder='../static',
                template_folder='../templates')

    from config import Config
    app.config.from_object(Config)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'instance'), exist_ok=True)

    db.init_app(app)

    from app.routes_client import client_bp
    from app.routes_admin import admin_bp
    app.register_blueprint(client_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        from app import models
        db.create_all()

    return app
