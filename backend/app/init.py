from flask import Flask
from flask_cors import CORS
from .config import Config
from .routes.main import routes  # 从 routes/main.py 中导入蓝图

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config.from_object(Config)

    # 注册蓝图
    app.register_blueprint(routes)

    return app
