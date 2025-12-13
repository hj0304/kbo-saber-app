from flask import Flask
from .routes.calc import bp as calc_bp
from .routes.pitch import bp as pitch_bp
from .routes.gamescore import bp as gamescore_bp
from .routes.pythag import bp as pythag_bp
from .routes.re24 import bp as re24_bp  # <-- 1. 이것을 추가
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.register_blueprint(calc_bp)
    app.register_blueprint(pitch_bp, url_prefix="/pitch")
    app.register_blueprint(gamescore_bp)          # /gamescore
    app.register_blueprint(pythag_bp)             # /pythag
    app.register_blueprint(re24_bp, url_prefix="/re24") # <-- 2. 이것을 추가
    return app