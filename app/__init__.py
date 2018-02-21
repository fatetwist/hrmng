from flask import Flask
from config import config
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from .main import main as main_blueprint
from .user import user as user_blueprint


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'user.login'
login_manager.login_message = '请先登录！'


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    login_manager.init_app(app)
    db.init_app(app)

    # 注册blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(user_blueprint, url_prefix='/user')




    return app
