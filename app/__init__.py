from flask import Flask
from .routes.calc import bp as calc_bp
from .routes.pitch import bp as pitch_bp  # 이미 있다면 유지
from .routes.gamescore import bp as gamescore_bp
from .routes.pythag import bp as pythag_bp
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.register_blueprint(calc_bp)
    app.register_blueprint(pitch_bp, url_prefix="/pitch")
    app.register_blueprint(gamescore_bp)          # /gamescore
    app.register_blueprint(pythag_bp)             # /pythag
    return app