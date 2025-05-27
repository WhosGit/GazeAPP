from flask import Flask
from flask_cors import CORS
# from .config import Config
from .views.main import routes  # 从 routes/main.py 中导入蓝图
from .api.main import api  # 从 api/main.py 中导入蓝图

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_object('app.config')

    # 注册蓝图
    app.register_blueprint(routes, url_prefix='/')
    app.register_blueprint(api, url_prefix='/api')

    return app

import app.utils
import app.views
import app.api
from app.model import *