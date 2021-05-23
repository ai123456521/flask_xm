# @ Time    : 2020/11/16 21:19


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import redis
from flask_session import Session
from flask_wtf import CSRFProtect

app = Flask(__name__)


class Config(object):
    """配置信息"""

    SECRET_KEY = 'ASDAXCWE5ERTFG%%DAS34'
    USERNAME = 'root'
    PASSWORD = 'root'
    HOSTNAME = '127.0.0.1'
    PORT     = 3306
    DATEBASE = 'home'

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # flask-session
    SESSION_TYPE = 'redis'

    SESSION_REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 8640   # 单位是秒

    # 数据库
    DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATEBASE)

app.config.from_object(Config)

db = SQLAlchemy(app)

# 创建Redis
redis_store = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT)

# session
Session(app)

# post请求  wtf  csrf
CSRFProtect(app)


@app.route('/')
def index():
    return "index page"


if __name__ == '__main__':
    app.run()