# @ Time    : 2020/11/20 20:44


from . import api
from lghome.utils.captcha.captcha import captcha
from lghome import redis_store
import logging
from flask import jsonify, make_response, request
from lghome import constants
from lghome.response_code import RET
from lghome.models import User
import random
from lghome.tasks.sms.tasks import send_sms

"""
REST风格
goods
/add_goods
/update_goods
/delete_goods
/get_goods

goods   
请求的方式
GET     查询
POST    保存
PUT     修改
DELETE  删除
"""


# UUID image_code_id
# 时间戳+随机数
# GET 127.0.0.1/api/v1.0/image_codes/<image_code_id>
# redis中数据类型
# UUID:验证码
# hash    image_code:{id:1, name:juran}
# string  uuid:xxxx
#   set key value
#   exprie
#   setex
# 过期时间
@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
    """
    获取图片验证码
    :param image_code_id: 图片的编号
    :return: 验证码,验证码图像
    """
    # 验证参数
    # 业务逻辑处理
    # 生成验证码图片
    text, image_data = captcha.generate_captcha()
    # 保存验证码
    # redis_store.set()
    # redis_store.exprie()
    try:
        redis_store.setex('image_code_%s' % image_code_id, constants.IAMGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片验证码失败')

    # 返回值
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'
    return response


@api.route("/sms_codes/<re(r'1[345678]\d{9}'):mobile>")
def get_sms_code(mobile):
    """获取短信验证码"""
    # 获取参数
    # 图片验证码
    image_code = request.args.get('image_code')
    # UUID
    image_code_id = request.args.get('image_code_id')

    # 校验参数
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 业务逻辑
    # 从redis中取出验证码
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')

    # 判断图片验证码是否过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码失效')

    # 删除redis中的图片验证码
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)

    # print(real_image_code)  b'RVMJ'
    # 与用户填写的图片验证码对比
    real_image_code = real_image_code.decode()
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')

    # 判断手机号的操作
    try:
        send_flag = redis_store.get('send_sms_code_%s' % mobile)
    except Exception as e:
        logging.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg='请求过于频繁')

    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
    else:
        if user is not None:
            # 表示手机号已经被注册过
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经存在')

    # 生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)

    # 保存真实的短信验证码到redis
    try:
        # redis管道
        pl = redis_store.pipeline()
        pl.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        # 保存发送给这个手机号的记录
        pl.setex('send_sms_code_%s' % mobile, constants.SNED_SMS_CODE_EXPIRES, 1)
        pl.execute()

    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存短信验证码异常')

    # 发短信
    # try:
    #     ccp = CCP()
    #     result = ccp.send_message(mobile, (sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)), 1)
    # except Exception as e:
    #     logging.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送异常')
    # from lghome.tasks.task_sms import send_sms

    send_sms.delay(mobile, (sms_code, int(constants.SMS_CODE_REDIS_EXPIRES / 60)), 1)

    # 返回值
    # if result == 0:
    return jsonify(errno=RET.OK, errmsg='发送成功')
    # else:
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送失败')
