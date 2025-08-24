from flask import Flask
from .routes.calc import bp as calc_bp
from .routes.pitch import bp as pitch_bp

def create_app():
    app = Flask(__name__)
    app.register_blueprint(calc_bp)
    app.register_blueprint(pitch_bp, url_prefix="/pitch")
    return app
