# @ Time    : 2020/11/30 20:54

from . import api
from lghome.utils.commons import login_required
from flask import g, request, jsonify, session
from lghome.response_code import RET
from lghome.libs.image_storage import storage
import logging
from lghome.models import Area, House, Facility, HouseImage, User, Order
from lghome import db, redis_store
from lghome import constants
import json
from datetime import datetime


@api.route("/areas")
def get_area_info():
    """获取城区信息"""

    # 用redis中读取数据
    try:
        response_json = redis_store.get("area_info")
    except Exception as e:
        logging.error(e)
    else:
        # redis有缓存数据
        if response_json is not None:
            response_json = json.loads(response_json)
            # print(response_json)
            logging.info('redis cache')
            # return response_json, 200, {"Content-Type": "application/json"}
            return jsonify(errno=RET.OK, errmsg='OK', data=response_json['data'])

    # 查询数据库,读取城区信息
    try:
        area_li = Area.query.all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    area_dict_li = []
    # print(area_li)
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 将数据转成json字符串  {key:value} <= dict(key=value)
    # response_dict = dict(errno=RET.OK, errmsg='OK', data=area_dict_li)
    response_dict = dict(data=area_dict_li)
    response_json = json.dumps(response_dict)

    try:
        redis_store.setex("area_info", constants.AREA_INFO_REDIS_CACHE_EXPIRES, response_json)
    except Exception as e:
        logging.error(e)

    # return response_json, 200, {"Content-Type": "application/json"}
    return jsonify(errno=RET.OK, errmsg='OK', data=area_dict_li)


@api.route("/houses/info", methods=["POST"])
@login_required
def save_house_info():
    """
    保存房屋的基本信息
    :return: 保存失败或者保存成功
    {
    "title":"1",
    "price":"1",
    "area_id":"8",
    "address":"1",
    "room_count":"1",
    "acreage":"1",
    "unit":"1",
    "capacity":"1",
    "beds":"1",
    "deposit":"1",
    "min_days":"1",
    "max_days":"1",
    "facility":["2","4"]
    }
    """
    # 发布房源的用户
    user_id = g.user_id

    house_data = request.get_json()
    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数 2
    max_days = house_data.get("max_days")  # 最大入住天数 1
    # facility = house_data.get("facility")  # 设备信息

    # 校验参数
    if not all([title, price, area_id, address, room_count, acreage, unit]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')

    # 判断价格是否正确
    try:
        price = int(float(price) * 100)  # 分
        deposit = int(float(deposit) * 100)  # 分
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 判断区域ID
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='数据库异常')

    if area is None:
        return jsonify(errno=RET.PARAMERR, errmsg='城区信息有误')

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    # 设施信息
    facility_ids = house_data.get("facility")

    if facility_ids:
        # ["23", "24"]
        # 查看设置是否存在
        # SELECT * FROM h_facility_info WHERE id IN (1,3, 5);
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库异常')

        if facilities:
            # 表示有合法的设备
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    # 返回结果
    return jsonify(errno=RET.OK, errmsg='OK', data={"house_id": house.id})


@api.route("/houses/image", methods=["POST"])
@login_required
def save_house_image():
    """
    保存房屋的图片
    :param:house_id 房屋的ID   house_image 房屋的图片
    :return: image_url 房屋图片地址
    """
    # 接收参数
    image_file = request.files.get("house_image")
    house_id = request.form.get("house_id")

    # 校验
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # 图片上传到七牛云
    image_data = image_file.read()
    try:
        filename = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='保存图片失败')

    # 保存图片信息到数据库(图片的名字)
    house_image = HouseImage(house_id=house_id, url=filename)
    db.session.add(house_image)

    # 处理房屋的主图
    if not house.index_image_url:
        house.index_image_url = filename
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')

    image_url = constants.QINIU_URL_DOMAIN + filename
    return jsonify(errno=RET.OK, errmsg='OK', data={"image_url": image_url})


@api.route("/user/houses", methods=["GET"])
@login_required
def get_user_houses():
    """
    获取用户发布的房源
    :return: 发布的房源信息
    """

    # 获取当前的用户
    user_id = g.user_id

    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')

    # 转成字典存放到列表中
    houses_list = []
    if houses:
        for house in houses:
            houses_list.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg="OK", data={"houses": houses_list})


@api.route("/houses/index", methods=["GET"])
def get_house_index():
    """
    获取首页房屋信息
    :return: 排序后的房屋信息
    """

    # 先查询缓存数据
    try:
        result = redis_store.get("home_page_data")
    except Exception as e:
        logging.error(e)
        result = None

    if result:
        # print("redis")
        return result.decode(), 200, {"Content-Type": "application/json"}
    else:
        try:
            # 查询数据库,房屋订单最多的5条
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_NUMS).all()
        except Exception as e:
            return jsonify(errno=RET.DBERR, errmsg="查询数据库失败")
        # [<House 1>, <House 2>]
        if not houses:
            return jsonify(errno=RET.NODATA, errmsg="查询没有数据")

        houses_list = []
        for house in houses:
            houses_list.append(house.to_basic_dict())

        house_dict = dict(errno=RET.OK, errmsg="OK", data=houses_list)
        json_houses = json.dumps(house_dict)

        try:
            redis_store.setex("home_page_data", constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            logging.error(e)

        # [<House 1>, <House 2>]
        return json_houses, 200, {"Content-Type": "application/json"}
        # return jsonify(errno=RET.OK, errmsg="OK", data=houses_list)


@api.route("/houses/<int:house_id>", methods=["GET"])
def get_house_detail(house_id):
    """
    获取房屋详情
    :param house_id: 房屋的ID
    :return: 房屋的详细信息
    """
    # 当前用户
    # g对象中
    user_id = session.get("user_id", "-1")

    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')

    # 先从缓存中查询数据
    try:
        result = redis_store.get("house_info_%s" % house_id)
    except Exception as e:
        logging.error(e)
        result = None

    if result:
        # dict(name=12)  {"name": 12}
        return '{"errno":%s, "errmsg":"OK", "data":{"house": %s, "user_id": %s}}' % (
        RET.OK, result.decode(), user_id), 200, {"Content-Type": "application/json"}

    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')

    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')

    # print(house)
    house_data = house.to_full_dict()

    # 存入redis
    json_house = json.dumps(house_data)
    try:
        redis_store.setex("house_info_%s" % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE, json_house)
    except Exception as e:
        logging.error(e)

    # print(house_data)
    return jsonify(errno=RET.OK, errmsg='OK', data={"house": house_data, "user_id": user_id})


# http://127.0.0.1:5000/api/v1.0/houses?aid=&sd=&ed=&sk=new&p=1
# aid   区域的id
# sd    开始时间
# ed    结束时间
# sk    排序
# p     页码

@api.route("/houses", methods=["GET"])
def get_house_list():
    """
    房屋的搜索页面
    :param: aid   区域的id   sd  开始时间  ed    结束时间  sk    排序  p  页码
    :return: 符合条件的房屋
    """
    # 接收参数
    start_date = request.args.get('sd')
    end_date = request.args.get('ed')
    area_id = request.args.get('aid')
    sort_key = request.args.get('sk')
    page = request.args.get('p')

    # 校验参数
    # 2020-12-04 字符串
    try:
        if start_date:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")

        if end_date:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

        # if start_date >= end_date:
        #     return jsonify(errno=RET.PARAMERR, errmsg='日期参数有误')
        if start_date and end_date:
            # 05 <= 04
            assert start_date <= end_date
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期参数有误')

    # if start_date and end_date:
    #     assert start_date <= end_date

    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='区域参数有误')

    # if sort_key in ["new"]:
    #     pass
    try:
        # 1.2
        page = int(page)
    except Exception as e:
        logging.error(e)
        page = 1

    # 查询缓存数据
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        logging.error(e)
    else:
        if resp_json:
            return resp_json.decode(), 200, {"Content-Type": "application/json"}

    # 查询数据库
    conflict_orders = None
    # 过滤条件
    filter_params = []

    try:
        if start_date and end_date:
            # 查询冲突的订单
            # order.begin_data  <= end_date and
            # order.end_date >= start_date
            conflict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')

    # print(conflict_orders)
    if conflict_orders:
        # 从订单中获取冲突的房屋ID
        conflict_house_id = [order.house_id for order in conflict_orders]

        if conflict_house_id:
            # house = House.query.filter(House.id.notin_(conflict_house_id))
            filter_params.append(House.id.notin_(conflict_house_id))

    if area_id:
        # 查询的条件
        filter_params.append(House.area_id == area_id)

    # 排序
    if sort_key == "booking":
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == "price-inc":
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == "price-des":
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 处理分页
    page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_NUMS, error_out=False)

    # 总页数
    total_page = page_obj.pages

    # 获取数据
    house_li = page_obj.items

    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    resp_dict = dict(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses})
    resp_json = json.dumps(resp_dict)

    # 将数据保存到redis中
    redis_key = "house_%s_%s_%s_%s" % (start_date, end_date, area_id, sort_key)
    try:
        # redis管道
        pipeline = redis_store.pipeline()

        pipeline.hset(redis_key, page, resp_json)
        pipeline.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
        pipeline.execute()

    except Exception as e:
        logging.error(e)

    return jsonify(errno=RET.OK, errmsg="OK", data={"total_page": total_page, "houses": houses})
    # house = House.query.filter(*filter_params)
    # print(house)

# 搜索的数据放到redis中
# 选择什么数据类型
# 字符串
# house_开始_结束_区域ID_排序_页数
# key value
# house_开始_结束_区域ID_排序 key
# value
# {
#   "1": {1, 2, 3},
#   "2": {1, 3}
# }
# hash
