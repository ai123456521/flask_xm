# @ Time    : 2020/11/20 21:26


# 图片验证码的redis有效期，单位:秒
IAMGE_CODE_REDIS_EXPIRES = 180

# 短信验证码的redis有效期,单位：秒
SMS_CODE_REDIS_EXPIRES = 300

# 短信验证码的过期时间 单位:秒
SNED_SMS_CODE_EXPIRES = 60

# 登录次数的最大值
LOGIN_ERROR_MAX_TIMES = 5

# 登录次数验证时间间隔
LOGIN_ERROR_FORBID_TIME = 600

# 七牛云域名
# QINIU_URL_DOMAIN = 'http://qp2wp8lmb.hd-bkt.clouddn.com/'

QINIU_URL_DOMAIN = 'http://qrakoed47.hd-bkt.clouddn.com/'

# 地区有效期过期时间
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页展示的房屋数量
HOME_PAGE_MAX_NUMS = 6

# 首页房屋轮播图过期时间
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 详情房屋信息过期时间
HOUSE_DETAIL_REDIS_EXPIRE = 7200

# 每页显示的数据量
HOUSE_LIST_PAGE_NUMS = 2

# 搜索页面缓存时间
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200

# 详情页面的评论数量
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 2