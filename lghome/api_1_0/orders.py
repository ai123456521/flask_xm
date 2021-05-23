# @ Time    : 2020/12/8 20:56

from . import api
from lghome.utils.commons import login_required
from flask import g, request, jsonify
from lghome.response_code import RET
import logging
from lghome.models import House, Order
from lghome import db
from datetime import datetime
from lghome import redis_store


@api.route("/orders", methods=["POST"])
@login_required
def save_order():
    """
    保存订单
    :param: start_date  end_date house_id
    :return: 保存订单的状态
    """
    # 接收参数
    user_id = g.user_id

    order_data = request.get_json()
    if not order_data:
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    start_date = order_data.get('start_date')
    end_date = order_data.get('end_date')
    house_id = order_data.get('house_id')

    # 校验参数
    if not all([start_date, end_date, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        assert start_date <= end_date
        # 预定的天数
        days = (end_date - start_date).days + 1

    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg="日期格式错误")

    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取房屋信息失败")

    if not house:
        return jsonify(errno=RET.NODATA, errmsg="房屋不存在")

    # 预定的房屋是否是房东自己
    if user_id == house.user_id:
        # 说明是房东自己
        return jsonify(errno=RET.ROLEERR, errmsg="不能预定自己的房间")

    # 查询时间冲突的订单数量
    try:
        count = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date,
                                   Order.house_id == house_id).count()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="订单数据有误")

    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg="房屋已经被预定")

    # 订单总金额
    amount = days * house.price

    # 保存订单数据
    order = Order(
        user_id=user_id,
        house_id=house_id,
        begin_date=start_date,
        end_date=end_date,
        days=days,
        house_price=house.price,
        amount=amount
    )

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

    return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_orders():
    """
    查询用户的订单信息
    :param: role 角色   custom  landlord
    :return: 订单的信息
    """
    user_id = g.user_id

    role = request.args.get("role", "")

    # print(role)

    try:
        if role == "landlord":
            # 房东
            # 先查询属于自己的房子
            houses = House.query.filter(House.user_id == user_id).all()
            houses_id = [house.id for house in houses]

            # 根据房子的ID 查询预定了自己房子的订单
            orders = Order.query.filter(Order.house_id.in_(houses_id)).order_by(Order.create_time.desc()).all()

        else:
            # 客户的身份
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询订单失败")

    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"orders": orders_dict_list})


@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
    """
    接单 拒单
    :param order_id: 订单ID
    :return: json
    """
    user_id = g.user_id

    # 接收参数
    request_data = request.get_json()
    if not request_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    action = request_data.get('action')

    if action not in ("accept", "reject"):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        # 根据订单号,查询数据库
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    # 保证房东只能修改自己的房子的订单
    if house.user_id != user_id:
        return jsonify(errno=RET.REQERRE, errmsg='操作无效')

    if action == "accept":
        # 接单
        order.status = "WAIT_PAYMENT"
    elif action == "reject":
        # 拒单
        order.status = "REJECTED"
        reason = request_data.get("reason")
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        order.comment = reason

    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    return jsonify(errno=RET.OK, errmsg='OK')


@api.route("/orders/<int:order_id>/comment", methods=["PUT"])
@login_required
def save_order_comment(order_id):
    """
    保存订单评论信息
    :param order_id: 订单ID
    :return: json
    """
    # 接收参数
    user_id = g.user_id
    request_data = request.get_json()
    comment = request_data.get("comment")

    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    try:
        order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_COMMENT",
                                   Order.user_id == user_id).first()
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')

    if not order:
        return jsonify(errno=RET.DBERR, errmsg='操作无效')

    try:
        order.status = "COMPLETE"
        order.comment = comment

        # 将房屋订单加1
        house.order_count += 1
        db.session.add(house)
        db.session.add(order)

        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')

    # 删除缓存
    try:
        redis_store.delete("house_info_%s" % order.house_id)
    except Exception as e:
        logging.error(e)

    return jsonify(errno=RET.OK, errmsg='OK')
