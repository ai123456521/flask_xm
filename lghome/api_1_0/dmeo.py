# @ Time    : 2020/11/16 22:07

from . import api
import logging


@api.route('/index')
def index():
    logging.warning('数据库连接失败')
    return "index page"


@api.route('/profile')
def profile():
    return '个人中心'
