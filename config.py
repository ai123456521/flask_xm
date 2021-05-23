# @ Time    : 2020/11/16 21:47

import redis


class Config(object):
    """配置信息"""

    SECRET_KEY = 'ASDAXCWE5ERTFG%%DAS34'
    USERNAME = 'root'
    PASSWORD = 'root'
    HOSTNAME = '127.0.0.1'
    PORT = 3306
    DATEBASE = 'home'

    # redis配置
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    # flask-session
    SESSION_TYPE = 'redis'

    SESSION_REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 8640  # 单位是秒

    # 数据库
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(USERNAME, PASSWORD, HOSTNAME, PORT, DATEBASE)
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevConfig(Config):
    """开发环境"""
    DEBUG = True


class ProConfig(Config):
    """生产环境"""


config_map = {
    'dev': DevConfig,
    'pro': ProConfig
}
